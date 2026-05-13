#!/usr/bin/env python3
"""
Validate and zip a PBIP directory into a distributable archive.

Usage:
    python package_pbip.py <project-dir> [--output <zip-path>]

Validates that all required PBIP files exist per the official Microsoft PBIP
format (including .platform files, PBIR definition/ folder, pages.json, etc.),
checks pointer consistency, and creates a zip archive of the project.
"""
import argparse
import ast
import json
import os
import sys
import zipfile


REQUIRED_TMDL_FILES = {"database.tmdl", "model.tmdl"}


def find_existing_pbip_projects(search_root):
    results = []
    for dirpath, dirnames, filenames in os.walk(search_root):
        if "generated-reports" in dirpath:
            continue
        for f in filenames:
            if f.endswith(".pbip"):
                results.append(os.path.join(dirpath, f))
        dirnames[:] = [
            d for d in dirnames
            if d not in (".git", "node_modules", "__pycache__", ".pbi")
        ]
    return results

TMDL_KEYWORDS = {
    "model", "table", "column", "measure", "partition", "relationship",
    "database", "culture", "ref", "annotation", "dataType", "lineageTag",
    "formatString", "sourceColumn", "summarizeBy", "isHidden", "mode",
    "fromColumn", "toColumn", "isActive", "compatibilityLevel",
    "defaultPowerBIDataSourceVersion", "discourageImplicitMeasures",
    "sourceQueryCulture", "displayFolder", "source", "dataAccessOptions",
    "legacyRedirects", "returnErrorValuesAsNull",
}


def validate_tmdl_file(file_path):
    errors = []
    rel_path = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        errors.append(f"TMDL {rel_path}: File is not valid UTF-8")
        return errors

    lines = content.split("\n")

    if rel_path == "model.tmdl":
        ref_lines = [ln for ln in lines if ln.startswith("ref ")]
        for i, ln in enumerate(ref_lines):
            parts = ln.split()
            if parts[0] == "ref" and len(parts) >= 3:
                if parts[1] == "table" and len(parts) > 3:
                    errors.append(
                        f"TMDL {rel_path}: Multiple ref declarations on one line: '{ln}'"
                    )
                elif parts[1] == "cultureInfo" and len(parts) > 3:
                    errors.append(
                        f"TMDL {rel_path}: Multiple ref declarations on one line: '{ln}'"
                    )

    if rel_path == "relationships.tmdl":
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            if stripped.startswith("lineageTag:"):
                errors.append(
                    f"TMDL {rel_path} line {i}: 'lineageTag' is not supported on relationships. "
                    f"The GUID must be the relationship name (e.g., 'relationship <guid>'), not a property."
                )

    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped and not stripped.startswith("//") and not stripped.startswith("---"):
            indent = line[:len(line) - len(stripped)]
            if indent and " " in indent and "\t" not in indent:
                if not stripped.startswith("let") and not stripped.startswith("in") and not stripped.startswith("Source") and "=" not in stripped[:20]:
                    pass

    first_line = lines[0].strip() if lines else ""
    if first_line:
        first_word = first_line.split()[0] if first_line.split() else ""
        valid_starts = {"model", "table", "database", "culture", "cultureInfo", "relationship", "ref", "annotation", "createOrReplace"}
        if first_word not in valid_starts:
            errors.append(
                f"TMDL {rel_path}: File does not start with a valid TMDL keyword (got '{first_word}')"
            )

    return errors


def validate_json_file(file_path):
    errors = []
    rel_path = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        errors.append(f"JSON {rel_path}: File is not valid UTF-8")
        return errors

    try:
        json.loads(content)
    except json.JSONDecodeError as e:
        errors.append(f"JSON {rel_path}: Invalid JSON syntax: {e}")

    return errors


def validate_python_file(file_path):
    errors = []
    rel_path = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        errors.append(f"Python {rel_path}: File is not valid UTF-8")
        return errors

    try:
        ast.parse(content, filename=file_path)
    except SyntaxError as e:
        errors.append(f"Python {rel_path}: Syntax error at line {e.lineno}: {e.msg}")

    return errors


def validate_markdown_file(file_path):
    warnings = []
    rel_path = os.path.basename(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        warnings.append(f"Markdown {rel_path}: File is not valid UTF-8")
        return warnings

    if not content.strip():
        warnings.append(f"Markdown {rel_path}: File is empty")

    return warnings


def validate_file_formats(project_dir):
    errors = []
    warnings = []

    for root, dirs, files in os.walk(project_dir):
        dirs[:] = [d for d in dirs if d != ".pbi"]
        for filename in files:
            file_path = os.path.join(root, filename)

            if filename.endswith(".tmdl"):
                errors.extend(validate_tmdl_file(file_path))

            elif filename.endswith(".json"):
                if filename in ("localSettings.json", "cache.abf"):
                    continue
                errors.extend(validate_json_file(file_path))

            elif filename.endswith(".py"):
                errors.extend(validate_python_file(file_path))

            elif filename.endswith(".md"):
                warnings.extend(validate_markdown_file(file_path))

    return errors, warnings


def validate_structure(project_dir):
    project_name = os.path.basename(project_dir)
    errors = []
    warnings = []

    pbip_file = os.path.join(project_dir, f"{project_name}.pbip")
    if not os.path.exists(pbip_file):
        errors.append(f"Missing project file: {project_name}.pbip")

    sm_dir = os.path.join(project_dir, f"{project_name}.SemanticModel")
    if not os.path.isdir(sm_dir):
        errors.append(f"Missing semantic model directory: {project_name}.SemanticModel/")
    else:
        pbism = os.path.join(sm_dir, "definition.pbism")
        if not os.path.exists(pbism):
            errors.append("Missing definition.pbism in SemanticModel")
        else:
            with open(pbism) as f:
                pbism_data = json.load(f)
            version = pbism_data.get("version", "")
            if not version.startswith("4"):
                warnings.append(
                    f"definition.pbism version is '{version}', expected '4.x' for TMDL format"
                )

        tmdl_scripts_dir = os.path.join(sm_dir, "TMDLScripts")
        if os.path.isdir(tmdl_scripts_dir):
            tmdl_script_files = [
                f for f in os.listdir(tmdl_scripts_dir)
                if f.endswith(".tmdl")
            ]
            if tmdl_script_files:
                warnings.append(
                    f"TMDLScripts folder present with {len(tmdl_script_files)} script(s)"
                )

        platform = os.path.join(sm_dir, ".platform")
        if not os.path.exists(platform):
            warnings.append("Missing .platform in SemanticModel (required for Fabric Git integration)")

        def_dir = os.path.join(sm_dir, "definition")
        if os.path.isdir(def_dir):
            for req in REQUIRED_TMDL_FILES:
                if not os.path.exists(os.path.join(def_dir, req)):
                    errors.append(f"Missing required TMDL file: definition/{req}")

            tables_dir = os.path.join(def_dir, "tables")
            if not os.path.isdir(tables_dir):
                errors.append("Missing tables/ directory in semantic model definition")
            else:
                tmdl_files = [f for f in os.listdir(tables_dir) if f.endswith(".tmdl")]
                if not tmdl_files:
                    warnings.append("No .tmdl files found in tables/ directory")
        else:
            errors.append("Missing definition/ directory in SemanticModel")

    report_dir = os.path.join(project_dir, f"{project_name}.Report")
    if not os.path.isdir(report_dir):
        errors.append(f"Missing report directory: {project_name}.Report/")
    else:
        pbir = os.path.join(report_dir, "definition.pbir")
        if not os.path.exists(pbir):
            errors.append("Missing definition.pbir in Report")
        else:
            with open(pbir) as f:
                pbir_data = json.load(f)
            expected_path = f"../{project_name}.SemanticModel"
            by_path = pbir_data.get("datasetReference", {}).get("byPath", {})
            if by_path and by_path.get("path") != expected_path:
                actual_path = by_path.get("path")
                errors.append(
                    f"Pointer mismatch in definition.pbir: "
                    f"expected '{expected_path}', got '{actual_path}'"
                )

        platform = os.path.join(report_dir, ".platform")
        if not os.path.exists(platform):
            warnings.append("Missing .platform in Report (required for Fabric Git integration)")

        report_def_dir = os.path.join(report_dir, "definition")
        if os.path.isdir(report_def_dir):
            report_json = os.path.join(report_def_dir, "report.json")
            if not os.path.exists(report_json):
                errors.append("Missing definition/report.json in Report")

            version_json = os.path.join(report_def_dir, "version.json")
            if not os.path.exists(version_json):
                warnings.append("Missing definition/version.json in Report")

            pages_dir = os.path.join(report_def_dir, "pages")
            if os.path.isdir(pages_dir):
                pages_json = os.path.join(pages_dir, "pages.json")
                if not os.path.exists(pages_json):
                    warnings.append("Missing definition/pages/pages.json in Report")

                page_dirs = [
                    d for d in os.listdir(pages_dir)
                    if os.path.isdir(os.path.join(pages_dir, d))
                ]
                if not page_dirs:
                    warnings.append("No page directories found in Report/definition/pages/")
                for pd in page_dirs:
                    page_json = os.path.join(pages_dir, pd, "page.json")
                    if not os.path.exists(page_json):
                        errors.append(f"Missing page.json in pages/{pd}/")
                    visuals_dir = os.path.join(pages_dir, pd, "visuals")
                    if os.path.isdir(visuals_dir):
                        visual_dirs = [
                            v for v in os.listdir(visuals_dir)
                            if os.path.isdir(os.path.join(visuals_dir, v))
                        ]
                        for vd in visual_dirs:
                            visual_json = os.path.join(visuals_dir, vd, "visual.json")
                            if not os.path.exists(visual_json):
                                errors.append(f"Missing visual.json in pages/{pd}/visuals/{vd}/")
            else:
                warnings.append("Missing pages/ directory in Report/definition/")
        else:
            errors.append("Missing definition/ directory in Report")

    format_errors, format_warnings = validate_file_formats(project_dir)
    errors.extend(format_errors)
    warnings.extend(format_warnings)

    return errors, warnings


def create_zip(project_dir, output_path=None):
    project_name = os.path.basename(project_dir)
    if output_path is None:
        output_path = f"{project_dir}.zip"

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(project_dir):
            dirs[:] = [d for d in dirs if d != ".pbi"]
            for file in files:
                if file == "localSettings.json" or file == "cache.abf":
                    continue
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, os.path.dirname(project_dir))
                zf.write(file_path, arcname)

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Validate and zip a PBIP project")
    parser.add_argument("project_dir", help="Path to the PBIP project directory")
    parser.add_argument("--output", "-o", help="Output zip file path (default: <project>.zip)")
    parser.add_argument("--validate-only", action="store_true", help="Only validate, do not create zip")
    args = parser.parse_args()

    project_dir = os.path.abspath(args.project_dir)
    if not os.path.isdir(project_dir):
        print(f"Error: {project_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    print(f"Validating PBIP structure: {project_dir}")
    errors, warnings = validate_structure(project_dir)

    for w in warnings:
        print(f"  WARNING: {w}")
    for e in errors:
        print(f"  ERROR: {e}")

    if errors:
        print(f"\nValidation FAILED with {len(errors)} error(s)")
        sys.exit(1)

    print(f"Validation PASSED ({len(warnings)} warning(s))")

    if args.validate_only:
        return

    zip_path = create_zip(project_dir, args.output)
    size_kb = os.path.getsize(zip_path) / 1024
    print(f"\nCreated archive: {zip_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
