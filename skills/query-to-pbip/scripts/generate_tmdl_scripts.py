#!/usr/bin/env python3
"""
Generate the consolidated TMDLScripts file from split definition/ TMDL files.

Usage:
    python generate_tmdl_scripts.py <semantic-model-dir>

Reads the split TMDL files from <semantic-model-dir>/definition/ and produces
a single consolidated file at <semantic-model-dir>/TMDLScripts/power-bi-semantic-model.tmdl
in the `createOrReplace` format that Power BI Desktop expects.

The consolidated file combines:
- model.tmdl (model properties, stripped of ref declarations)
- tables/*.tmdl (all table definitions with columns, measures, partitions)
- relationships.tmdl (all relationship definitions)
- cultures/en-US.tmdl (culture info)
- model-level annotations from model.tmdl
"""
import os
import re
import sys


def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def indent_block(text, extra_tab_count=1):
    prefix = "\t" * extra_tab_count
    lines = text.split("\n")
    result = []
    for line in lines:
        if line.strip():
            result.append(prefix + line)
        else:
            result.append("")
    return "\n".join(result)


def parse_model_tmdl(content):
    lines = content.split("\n")
    model_props = []
    annotations = []
    ref_tables = []
    in_model_block = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("model Model"):
            in_model_block = True
            continue
        if stripped.startswith("ref table "):
            ref_tables.append(stripped.replace("ref table ", ""))
            continue
        if stripped.startswith("ref cultureInfo"):
            continue
        if stripped.startswith("annotation "):
            annotations.append(line)
            continue
        if in_model_block and (stripped.startswith("\t") or line.startswith("\t") or stripped):
            if stripped:
                model_props.append(line)

    return model_props, annotations, ref_tables


def parse_table_tmdl(content):
    lines = content.rstrip("\n").split("\n")
    return "\n".join(lines)


def parse_relationships_tmdl(content):
    if not content.strip():
        return ""
    lines = content.rstrip("\n").split("\n")
    return "\n".join(lines)


def parse_culture_tmdl(content):
    lines = content.rstrip("\n").split("\n")
    return "\n".join(lines)


def generate_consolidated(sm_dir):
    definition_dir = os.path.join(sm_dir, "definition")
    tables_dir = os.path.join(definition_dir, "tables")
    cultures_dir = os.path.join(definition_dir, "cultures")

    model_path = os.path.join(definition_dir, "model.tmdl")
    relationships_path = os.path.join(definition_dir, "relationships.tmdl")

    if not os.path.exists(model_path):
        print(f"Error: model.tmdl not found at {model_path}", file=sys.stderr)
        return None

    model_content = read_file(model_path)
    model_props, annotations, table_order = parse_model_tmdl(model_content)

    output_lines = ["createOrReplace", ""]

    model_header = ["\tmodel Model"]
    for prop in model_props:
        if prop.strip():
            if not prop.startswith("\t"):
                model_header.append("\t\t" + prop.strip())
            else:
                model_header.append("\t" + prop)
    output_lines.extend(model_header)
    output_lines.append("")

    if os.path.isdir(tables_dir):
        table_files = sorted(os.listdir(tables_dir))
        if table_order:
            ordered = []
            for name in table_order:
                fname = name + ".tmdl"
                if fname in table_files:
                    ordered.append(fname)
            for fname in table_files:
                if fname not in ordered:
                    ordered.append(fname)
            table_files = ordered

        for fname in table_files:
            if not fname.endswith(".tmdl"):
                continue
            fpath = os.path.join(tables_dir, fname)
            table_content = read_file(fpath).rstrip("\n")
            indented = indent_block(table_content, extra_tab_count=2)
            output_lines.append(indented)
            output_lines.append("")

    if os.path.exists(relationships_path):
        rel_content = read_file(relationships_path).strip()
        if rel_content:
            for block in re.split(r"\n(?=relationship )", rel_content):
                block = block.strip()
                if block:
                    indented = indent_block(block, extra_tab_count=2)
                    output_lines.append(indented)
                    output_lines.append("")

    if os.path.isdir(cultures_dir):
        for fname in sorted(os.listdir(cultures_dir)):
            if not fname.endswith(".tmdl"):
                continue
            fpath = os.path.join(cultures_dir, fname)
            culture_content = read_file(fpath).strip()
            if culture_content:
                indented = indent_block(culture_content, extra_tab_count=2)
                output_lines.append(indented)
                output_lines.append("")

    for ann in annotations:
        stripped = ann.strip()
        output_lines.append("\t\t" + stripped)
        output_lines.append("")

    result = "\n".join(output_lines).rstrip("\n") + "\n"
    return result


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python generate_tmdl_scripts.py <semantic-model-dir>",
            file=sys.stderr,
        )
        sys.exit(1)

    sm_dir = sys.argv[1]
    if not os.path.isdir(sm_dir):
        print(f"Error: {sm_dir} is not a directory", file=sys.stderr)
        sys.exit(1)

    tmdl_scripts_dir = os.path.join(sm_dir, "TMDLScripts")
    os.makedirs(tmdl_scripts_dir, exist_ok=True)

    consolidated = generate_consolidated(sm_dir)
    if consolidated is None:
        sys.exit(1)

    output_path = os.path.join(tmdl_scripts_dir, "power-bi-semantic-model.tmdl")
    with open(output_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(consolidated)

    print(f"Generated consolidated TMDL: {output_path}")
    print(f"  Size: {len(consolidated)} bytes")


if __name__ == "__main__":
    main()
