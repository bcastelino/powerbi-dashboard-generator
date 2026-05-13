#!/usr/bin/env python3
"""
Compose a multi-visual Power BI dashboard from already generated reports.

Usage:
    python compose_dashboard.py <dashboard-name> \
      --reports-dir generated-reports \
      --output generated-dashboards \
      --reports report1 report2 report3 ...

Creates a complete PBIP dashboard project by:
1. Discovering visuals from specified reports
2. Filtering out excluded visual types (cardVisual, slicer, kpi)
3. Validating semantic model consistency across reports
4. Paginating visuals (max 4 per page in a 2x2 grid)
5. Scaffolding the full PBIP directory structure
"""
import argparse
import copy
import json
import os
import re
import shutil
import sys
import uuid


EXCLUDED_VISUAL_TYPES = {"cardVisual", "slicer", "kpi"}

GRID_POSITIONS = [
    {"x": 0,   "y": 0,   "z": 0, "height": 360, "width": 640, "tabOrder": 0},
    {"x": 640, "y": 0,   "z": 1, "height": 360, "width": 640, "tabOrder": 1000},
    {"x": 0,   "y": 360, "z": 2, "height": 360, "width": 640, "tabOrder": 2000},
    {"x": 640, "y": 360, "z": 3, "height": 360, "width": 640, "tabOrder": 3000},
]

VISUAL_SCHEMA_VERSION = "2.6.0"
VISUAL_SCHEMA_URL = (
    "https://developer.microsoft.com/json-schemas/fabric/item/report/"
    "definition/visualContainer/2.6.0/schema.json"
)

PAGE_WIDTH = 1280
PAGE_HEIGHT = 720
MAX_VISUALS_PER_PAGE = 4


# ---------------------------------------------------------------------------
# Visual discovery
# ---------------------------------------------------------------------------

def discover_visuals(reports_dir, report_names):
    """Walk specified reports and return list of visual info dicts."""
    visuals = []
    for report_name in report_names:
        report_root = os.path.join(reports_dir, report_name)
        if not os.path.isdir(report_root):
            print(
                f"Warning: report directory not found: {report_root}",
                file=sys.stderr,
            )
            continue

        pages_dir = os.path.join(
            report_root,
            f"{report_name}.Report",
            "definition",
            "pages",
        )
        if not os.path.isdir(pages_dir):
            print(
                f"Warning: pages directory not found: {pages_dir}",
                file=sys.stderr,
            )
            continue

        for page_id in sorted(os.listdir(pages_dir)):
            page_path = os.path.join(pages_dir, page_id)
            if not os.path.isdir(page_path):
                continue
            visuals_dir = os.path.join(page_path, "visuals")
            if not os.path.isdir(visuals_dir):
                continue
            for visual_id in sorted(os.listdir(visuals_dir)):
                vj = os.path.join(visuals_dir, visual_id, "visual.json")
                if not os.path.isfile(vj):
                    continue
                with open(vj, "r") as f:
                    data = json.load(f)
                visual_type = data.get("visual", {}).get("visualType", "")
                visuals.append({
                    "report_name": report_name,
                    "page_id": page_id,
                    "visual_id": visual_id,
                    "visual_type": visual_type,
                    "source_path": vj,
                    "data": data,
                })
    return visuals


def filter_visuals(visuals):
    """Remove excluded visual types."""
    return [v for v in visuals if v["visual_type"] not in EXCLUDED_VISUAL_TYPES]


# ---------------------------------------------------------------------------
# Semantic model validation
# ---------------------------------------------------------------------------

def get_semantic_model_dir(reports_dir, report_name):
    """Return the SemanticModel definition dir for a report."""
    pbir_path = os.path.join(
        reports_dir, report_name,
        f"{report_name}.Report", "definition.pbir",
    )
    if not os.path.isfile(pbir_path):
        return None

    with open(pbir_path, "r") as f:
        pbir = json.load(f)

    rel_path = pbir.get("datasetReference", {}).get("byPath", {}).get("path", "")
    # rel_path is like "../<Name>.SemanticModel"
    sm_dir = os.path.normpath(
        os.path.join(
            reports_dir, report_name, f"{report_name}.Report", rel_path
        )
    )
    return sm_dir


def read_file_text(path):
    """Read a file and return its text, or None if missing."""
    if not os.path.isfile(path):
        return None
    with open(path, "r") as f:
        return f.read()


def collect_tmdl_content(sm_dir):
    """Collect key TMDL content for comparison."""
    content = {}
    definition_dir = os.path.join(sm_dir, "definition")

    for name in ("model.tmdl", "relationships.tmdl"):
        path = os.path.join(definition_dir, name)
        text = read_file_text(path)
        if text is not None:
            content[name] = text

    tables_dir = os.path.join(definition_dir, "tables")
    if os.path.isdir(tables_dir):
        for tfile in sorted(os.listdir(tables_dir)):
            if tfile.endswith(".tmdl"):
                text = read_file_text(os.path.join(tables_dir, tfile))
                if text is not None:
                    content[f"tables/{tfile}"] = text

    return content


def extract_measure_blocks(tmdl_text):
    """Return {name: block_text} for every measure defined in a TMDL file."""
    blocks = {}
    lines = tmdl_text.split("\n")
    measure_indices = []
    stop_index = len(lines)
    for i, line in enumerate(lines):
        if re.match(r"^\tmeasure '", line):
            m = re.match(r"^\tmeasure '([^']+)'", line)
            if m:
                measure_indices.append((i, m.group(1)))
        elif re.match(r"^\t(column |partition )", line):
            stop_index = i
            break
    for idx, (start, name) in enumerate(measure_indices):
        end = (
            measure_indices[idx + 1][0]
            if idx + 1 < len(measure_indices)
            else stop_index
        )
        block_lines = lines[start:end]
        while block_lines and not block_lines[-1].strip():
            block_lines.pop()
        blocks[name] = "\n".join(block_lines)
    return blocks


def merge_table_tmdl(base_tmdl, other_tmdl_list):
    """Return base_tmdl with any missing measures from other_tmdl_list appended."""
    base_names = set(
        re.findall(r"^\tmeasure '([^']+)'", base_tmdl, re.MULTILINE)
    )
    extra_blocks = []
    for other_tmdl in other_tmdl_list:
        for name, block in extract_measure_blocks(other_tmdl).items():
            if name not in base_names:
                extra_blocks.append(block)
                base_names.add(name)
    if not extra_blocks:
        return base_tmdl
    lines = base_tmdl.split("\n")
    insert_idx = len(lines)
    for i, line in enumerate(lines):
        if re.match(r"^\t(column |partition )", line):
            insert_idx = i
            break
    extra_lines = []
    for block in extra_blocks:
        extra_lines.extend(block.split("\n"))
        extra_lines.append("")
    return "\n".join(lines[:insert_idx] + extra_lines + lines[insert_idx:])


def merge_all_table_measures(source_sm_dirs, dashboard_sm_dir):
    """Merge missing DAX measures from all source SMs into the dashboard SM."""
    tables_dir = os.path.join(dashboard_sm_dir, "definition", "tables")
    if not os.path.isdir(tables_dir):
        return
    for tfile in sorted(os.listdir(tables_dir)):
        if not tfile.endswith(".tmdl"):
            continue
        dash_path = os.path.join(tables_dir, tfile)
        base_tmdl = read_file_text(dash_path)
        if base_tmdl is None:
            continue
        other_tmdls = [
            read_file_text(os.path.join(sm_dir, "definition", "tables", tfile))
            for sm_dir in source_sm_dirs
            if os.path.isfile(
                os.path.join(sm_dir, "definition", "tables", tfile)
            )
        ]
        other_tmdls = [t for t in other_tmdls if t]
        merged = merge_table_tmdl(base_tmdl, other_tmdls)
        if merged != base_tmdl:
            with open(dash_path, "w", newline="\n") as f:
                f.write(merged)
            print(f"  Merged missing measures into {tfile}")


def validate_semantic_models(reports_dir, report_names):
    """Ensure all reports share compatible semantic models.

    Validates that relationships.tmdl is identical across all reports
    (structural consistency), then returns the richest semantic model
    (superset of all measures) as the dashboard source.

    Returns (True, sm_dir_of_richest) on success, or (False, error_msg) on failure.
    """
    reference_relationships = None
    reference_report = None
    richest_sm_dir = None
    richest_content_size = -1
    all_sm_dirs = []
    incompatible = []

    for report_name in report_names:
        sm_dir = get_semantic_model_dir(reports_dir, report_name)
        if sm_dir is None or not os.path.isdir(sm_dir):
            incompatible.append(
                (report_name, "SemanticModel directory not found")
            )
            continue

        all_sm_dirs.append(sm_dir)
        content = collect_tmdl_content(sm_dir)

        relationships = content.get("relationships.tmdl", "")
        if reference_relationships is None:
            reference_relationships = relationships
            reference_report = report_name
        else:
            if relationships != reference_relationships:
                incompatible.append(
                    (report_name,
                     f"relationships.tmdl differs from {reference_report}")
                )

        content_size = sum(len(v) for v in content.values())
        if content_size > richest_content_size:
            richest_content_size = content_size
            richest_sm_dir = sm_dir

    if incompatible:
        lines = ["Semantic model inconsistency detected:"]
        for name, reason in incompatible:
            lines.append(f"  - {name}: {reason}")
        return False, "\n".join(lines)

    return True, (richest_sm_dir, all_sm_dirs)


# ---------------------------------------------------------------------------
# PBIP scaffolding helpers
# ---------------------------------------------------------------------------

def new_page_id():
    return uuid.uuid4().hex[:20]


def create_pbip_pointer(project_name):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
        "version": "1.0",
        "artifacts": [
            {
                "report": {
                    "path": f"{project_name}.Report"
                }
            }
        ],
        "settings": {
            "enableAutoRecovery": True
        }
    }


def create_pbir_pointer(project_name):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
        "version": "4.0",
        "datasetReference": {
            "byPath": {
                "path": f"../{project_name}.SemanticModel"
            }
        }
    }


def create_report_json():
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json",
        "themeCollection": {
            "baseTheme": {
                "name": "CY25SU11",
                "reportVersionAtImport": {
                    "visual": "2.4.0",
                    "report": "3.0.0",
                    "page": "2.3.0"
                },
                "type": "SharedResources"
            }
        },
        "objects": {
            "outspacePane": [
                {
                    "properties": {
                        "expanded": {
                            "expr": {
                                "Literal": {
                                    "Value": "false"
                                }
                            }
                        }
                    }
                }
            ]
        },
        "resourcePackages": [
            {
                "name": "SharedResources",
                "type": "SharedResources",
                "items": [
                    {
                        "name": "CY25SU11",
                        "path": "BaseThemes/CY25SU11.json",
                        "type": "BaseTheme"
                    }
                ]
            }
        ],
        "settings": {
            "useStylableVisualContainerHeader": True,
            "exportDataMode": "AllowSummarized",
            "defaultDrillFilterOtherVisuals": True,
            "allowChangeFilterTypes": True,
            "useEnhancedTooltips": True,
            "useDefaultAggregateDisplayName": True
        }
    }


def create_version_json():
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
        "version": "2.0.0"
    }


def create_pages_json(page_ids):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": page_ids,
        "activePageName": page_ids[0] if page_ids else ""
    }


def create_page_json(page_id, display_name="Page 1"):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": page_id,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": PAGE_HEIGHT,
        "width": PAGE_WIDTH
    }


def write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="\n") as f:
        json.dump(data, f, indent=2)
        f.write("\n")


def apply_position(visual_data, position, visual_id):
    """Update a visual.json dict with new position and schema version."""
    visual_data["$schema"] = VISUAL_SCHEMA_URL
    visual_data["name"] = visual_id
    visual_data["position"] = {
        "x": position["x"],
        "y": position["y"],
        "z": position["z"],
        "height": position["height"],
        "width": position["width"],
        "tabOrder": position["tabOrder"],
    }
    return visual_data


# ---------------------------------------------------------------------------
# CY25SU11 theme loader
# ---------------------------------------------------------------------------

def find_theme_file(reports_dir, report_names):
    """Find the CY25SU11.json theme from one of the source reports."""
    for report_name in report_names:
        theme_path = os.path.join(
            reports_dir, report_name,
            f"{report_name}.Report",
            "StaticResources", "SharedResources",
            "BaseThemes", "CY25SU11.json",
        )
        if os.path.isfile(theme_path):
            return theme_path
    # Fallback: check the sample dashboard
    sample_theme = os.path.join(
        os.path.dirname(reports_dir),
        "generated-dashboards", "MonthlyUsersDash",
        "MonthlyUsersDash.Report",
        "StaticResources", "SharedResources",
        "BaseThemes", "CY25SU11.json",
    )
    if os.path.isfile(sample_theme):
        return sample_theme
    return None


# ---------------------------------------------------------------------------
# Main composition
# ---------------------------------------------------------------------------

def compose_dashboard(dashboard_name, reports_dir, output_dir, report_names):
    """Compose the dashboard and write to output_dir."""

    # Ensure Dash suffix
    if not dashboard_name.endswith("Dash"):
        dashboard_name = dashboard_name + "Dash"

    # 1. Discover visuals
    print(f"Discovering visuals from {len(report_names)} report(s)...")
    all_visuals = discover_visuals(reports_dir, report_names)
    print(f"  Found {len(all_visuals)} total visual(s)")

    # 2. Filter excluded types
    filtered = filter_visuals(all_visuals)
    excluded_count = len(all_visuals) - len(filtered)
    print(f"  Excluded {excluded_count} visual(s) (cardVisual/slicer/kpi)")
    print(f"  Remaining: {len(filtered)} visual(s)")

    if not filtered:
        print(
            "Error: No visuals remaining after filtering.",
            file=sys.stderr,
        )
        sys.exit(1)

    # 3. Validate semantic models
    print("Validating semantic model consistency...")
    ok, result = validate_semantic_models(reports_dir, report_names)
    if not ok:
        print(f"Error: {result}", file=sys.stderr)
        sys.exit(1)
    source_sm_dir, all_sm_dirs = result
    print("  All semantic models are consistent.")

    # 4. Paginate
    pages = []
    for i in range(0, len(filtered), MAX_VISUALS_PER_PAGE):
        pages.append(filtered[i:i + MAX_VISUALS_PER_PAGE])
    print(f"  Layout: {len(filtered)} visual(s) across {len(pages)} page(s)")

    # 5. Scaffold output
    root = os.path.join(output_dir, dashboard_name)
    if os.path.exists(root):
        shutil.rmtree(root)

    report_dir = os.path.join(root, f"{dashboard_name}.Report")
    sm_dir = os.path.join(root, f"{dashboard_name}.SemanticModel")
    definition_dir = os.path.join(report_dir, "definition")
    pages_dir = os.path.join(definition_dir, "pages")

    # Create directories
    os.makedirs(pages_dir, exist_ok=True)
    os.makedirs(os.path.join(sm_dir, ".pbi"), exist_ok=True)
    os.makedirs(
        os.path.join(sm_dir, "definition", "tables"), exist_ok=True
    )
    os.makedirs(
        os.path.join(sm_dir, "definition", "cultures"), exist_ok=True
    )

    # Write .pbip
    write_json(
        os.path.join(root, f"{dashboard_name}.pbip"),
        create_pbip_pointer(dashboard_name),
    )

    # Write .gitignore
    gitignore_path = os.path.join(root, ".gitignore")
    with open(gitignore_path, "w", newline="\n") as f:
        f.write("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")

    # Copy semantic model from source report
    print(f"  Copying semantic model from: {source_sm_dir}")
    for item in os.listdir(source_sm_dir):
        src = os.path.join(source_sm_dir, item)
        dst = os.path.join(sm_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)

    # Merge missing DAX measures from all source semantic models
    print("  Merging missing measures from all source semantic models...")
    merge_all_table_measures(all_sm_dirs, sm_dir)

    # Write definition.pbir
    write_json(
        os.path.join(report_dir, "definition.pbir"),
        create_pbir_pointer(dashboard_name),
    )

    # Write report.json
    write_json(
        os.path.join(definition_dir, "report.json"),
        create_report_json(),
    )

    # Write version.json
    write_json(
        os.path.join(definition_dir, "version.json"),
        create_version_json(),
    )

    # Write CY25SU11.json theme
    theme_source = find_theme_file(reports_dir, report_names)
    theme_dest = os.path.join(
        report_dir, "StaticResources", "SharedResources",
        "BaseThemes", "CY25SU11.json",
    )
    os.makedirs(os.path.dirname(theme_dest), exist_ok=True)
    if theme_source:
        shutil.copy2(theme_source, theme_dest)
    else:
        print(
            "  Warning: CY25SU11.json theme not found, "
            "creating minimal placeholder.",
            file=sys.stderr,
        )
        write_json(theme_dest, {"name": "CY25SU11"})

    # Create pages with visuals
    page_ids = []
    for page_idx, page_visuals in enumerate(pages):
        page_id = new_page_id()
        page_ids.append(page_id)
        page_dir = os.path.join(pages_dir, page_id)
        os.makedirs(page_dir, exist_ok=True)

        display_name = f"Page {page_idx + 1}"
        write_json(
            os.path.join(page_dir, "page.json"),
            create_page_json(page_id, display_name),
        )

        for vis_idx, vis_info in enumerate(page_visuals):
            visual_id = uuid.uuid4().hex[:20]
            vis_dir = os.path.join(page_dir, "visuals", visual_id)
            os.makedirs(vis_dir, exist_ok=True)

            visual_data = copy.deepcopy(vis_info["data"])
            position = GRID_POSITIONS[vis_idx]
            visual_data = apply_position(visual_data, position, visual_id)

            write_json(
                os.path.join(vis_dir, "visual.json"), visual_data
            )

    # Write pages.json
    write_json(
        os.path.join(pages_dir, "pages.json"),
        create_pages_json(page_ids),
    )

    # Summary
    print(f"\nDashboard created: {root}")
    print(f"  {dashboard_name}.pbip")
    print(f"  .gitignore")
    print(f"  {dashboard_name}.SemanticModel/")
    print(f"    .pbi/editorSettings.json")
    print(f"    definition/model.tmdl")
    print(f"    definition/relationships.tmdl")
    print(f"    definition/cultures/en-US.tmdl")
    print(f"    definition/tables/*.tmdl")
    print(f"  {dashboard_name}.Report/")
    print(
        f"    definition.pbir "
        f"(-> ../{dashboard_name}.SemanticModel)"
    )
    print(f"    definition/report.json")
    print(f"    definition/version.json")
    print(
        f"    StaticResources/SharedResources/"
        f"BaseThemes/CY25SU11.json"
    )
    for page_idx, page_id in enumerate(page_ids):
        vis_count = len(pages[page_idx])
        print(
            f"    definition/pages/{page_id}/ "
            f"(Page {page_idx + 1}: {vis_count} visual(s))"
        )

    print(
        f"\nTotal: {len(filtered)} visual(s) across "
        f"{len(pages)} page(s)"
    )


def main():
    parser = argparse.ArgumentParser(
        description=(
            "Compose a multi-visual Power BI dashboard "
            "from generated reports"
        )
    )
    parser.add_argument(
        "dashboard_name",
        help=(
            "Name of the dashboard "
            "(Dash suffix appended automatically if missing)"
        ),
    )
    parser.add_argument(
        "--reports-dir",
        default="generated-reports",
        help=(
            "Directory containing generated reports "
            "(default: generated-reports)"
        ),
    )
    parser.add_argument(
        "--output",
        default="generated-dashboards",
        help=(
            "Output directory for the dashboard "
            "(default: generated-dashboards)"
        ),
    )
    parser.add_argument(
        "--reports",
        nargs="+",
        required=True,
        help="Names of reports to pull visuals from",
    )
    args = parser.parse_args()

    compose_dashboard(
        args.dashboard_name,
        args.reports_dir,
        args.output,
        args.reports,
    )


if __name__ == "__main__":
    main()
