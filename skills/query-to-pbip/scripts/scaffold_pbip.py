#!/usr/bin/env python3
"""
Scaffold a PBIP directory structure with all required files.

Usage:
    python scaffold_pbip.py <project-name> --output <output-dir>

Creates the complete PBIP directory hierarchy matching the official Microsoft
PBIP format with TMDL semantic model and PBIR report format, including:
- .platform files for Fabric Git integration
- definition.pbism (version 4.2) for TMDL format
- definition.pbir (version 4.0) for PBIR format
- definition/ folder structure for report (pages, visuals)
- .gitignore for local settings and cache files
"""
import argparse
import json
import os
import shutil
import sys
import uuid


def new_guid():
    return str(uuid.uuid4())


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


def create_pbism_pointer():
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
        "version": "4.2",
        "settings": {}
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


def create_platform_file(item_type, display_name):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
        "metadata": {
            "type": item_type,
            "displayName": display_name
        },
        "config": {
            "version": "2.0",
            "logicalId": new_guid()
        }
    }


def create_editor_settings():
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/editorSettings/1.0.0/schema.json",
        "autodetectRelationships": True,
        "parallelQueryLoading": True,
        "typeDetectionEnabled": True,
        "relationshipImportEnabled": True,
        "shouldNotifyUserOfNameConflictResolution": True
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


def create_pages_json(page_id):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
        "pageOrder": [page_id],
        "activePageName": page_id
    }


def create_page_json(page_id, display_name="Page 1"):
    return {
        "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
        "name": page_id,
        "displayName": display_name,
        "displayOption": "FitToPage",
        "height": 720,
        "width": 1280
    }


def create_tmdl_scripts_json(script_name="power-bi-semantic-model"):
    return {
        "version": "1.0.0",
        "tabOrder": [script_name],
        "defaultTab": script_name
    }


def create_gitignore():
    return "**/.pbi/localSettings.json\n**/.pbi/cache.abf\n"


def find_semantic_models(search_root):
    results = []
    for dirpath, dirnames, filenames in os.walk(search_root):
        if "generated-reports" in dirpath or "generated-dashboards" in dirpath:
            continue
        for d in dirnames:
            if d.endswith(".SemanticModel"):
                full_path = os.path.join(dirpath, d)
                results.append(full_path)
        dirnames[:] = [
            d for d in dirnames
            if d not in (".git", "node_modules", "__pycache__", ".pbi")
        ]
    return results


def copy_semantic_model(source_sm_dir, dest_sm_dir):
    for item in os.listdir(source_sm_dir):
        src = os.path.join(source_sm_dir, item)
        dst = os.path.join(dest_sm_dir, item)
        if os.path.isdir(src):
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
        else:
            shutil.copy2(src, dst)
    print(f"  Copied SemanticModel contents from: {source_sm_dir}")


def scaffold(project_name, output_dir, repo_root=None, semantic_model_path=None):
    root = os.path.join(output_dir, project_name)
    page_id = uuid.uuid4().hex[:20]

    dirs = [
        root,
        os.path.join(root, f"{project_name}.SemanticModel"),
        os.path.join(root, f"{project_name}.SemanticModel", ".pbi"),
        os.path.join(root, f"{project_name}.SemanticModel", "definition"),
        os.path.join(root, f"{project_name}.SemanticModel", "definition", "tables"),
        os.path.join(root, f"{project_name}.SemanticModel", "definition", "cultures"),
        os.path.join(root, f"{project_name}.SemanticModel", "TMDLScripts"),
        os.path.join(root, f"{project_name}.SemanticModel", "TMDLScripts", ".pbi"),
        os.path.join(root, f"{project_name}.Report"),
        os.path.join(root, f"{project_name}.Report", "definition"),
        os.path.join(root, f"{project_name}.Report", "definition", "pages"),
        os.path.join(root, f"{project_name}.Report", "definition", "pages", page_id),
        os.path.join(root, f"{project_name}.Report", "definition", "pages", page_id, "visuals"),
        os.path.join(root, f"{project_name}.Report", "StaticResources", "SharedResources", "BaseThemes"),
    ]

    for d in dirs:
        os.makedirs(d, exist_ok=True)

    files = {
        os.path.join(root, f"{project_name}.pbip"):
            create_pbip_pointer(project_name),
        os.path.join(root, f"{project_name}.SemanticModel", "definition.pbism"):
            create_pbism_pointer(),
        os.path.join(root, f"{project_name}.SemanticModel", ".platform"):
            create_platform_file("SemanticModel", project_name),
        os.path.join(root, f"{project_name}.SemanticModel", ".pbi", "editorSettings.json"):
            create_editor_settings(),
        os.path.join(root, f"{project_name}.SemanticModel", "TMDLScripts", ".pbi", "tmdlScripts.json"):
            create_tmdl_scripts_json(),
        os.path.join(root, f"{project_name}.Report", "definition.pbir"):
            create_pbir_pointer(project_name),
        os.path.join(root, f"{project_name}.Report", ".platform"):
            create_platform_file("Report", project_name),
        os.path.join(root, f"{project_name}.Report", "definition", "report.json"):
            create_report_json(),
        os.path.join(root, f"{project_name}.Report", "definition", "version.json"):
            create_version_json(),
        os.path.join(root, f"{project_name}.Report", "definition", "pages", "pages.json"):
            create_pages_json(page_id),
        os.path.join(root, f"{project_name}.Report", "definition", "pages", page_id, "page.json"):
            create_page_json(page_id),
    }

    for path, content in files.items():
        with open(path, "w", newline="\n") as f:
            json.dump(content, f, indent=2)
            f.write("\n")

    gitignore_path = os.path.join(root, ".gitignore")
    with open(gitignore_path, "w", newline="\n") as f:
        f.write("**/.pbi/localSettings.json\n**/.pbi/cache.abf\n")

    culture_path = os.path.join(
        root, f"{project_name}.SemanticModel", "definition", "cultures", "en-US.tmdl"
    )
    with open(culture_path, "w", newline="\n") as f:
        f.write(
            'cultureInfo en-US\n'
            '\n'
            '\tlinguisticMetadata =\n'
            '\t\t\t{\n'
            '\t\t\t  "Version": "1.0.0",\n'
            '\t\t\t  "Language": "en-US"\n'
            '\t\t\t}\n'
            '\t\tcontentType: json\n'
        )

    sm_dir = os.path.join(root, f"{project_name}.SemanticModel")
    if semantic_model_path:
        copy_semantic_model(semantic_model_path, sm_dir)
    elif repo_root:
        existing = find_semantic_models(repo_root)
        if len(existing) == 1:
            print(f"  Found existing SemanticModel: {existing[0]}")
            copy_semantic_model(existing[0], sm_dir)
        elif len(existing) > 1:
            print("  Multiple SemanticModel folders found:")
            for i, sm in enumerate(existing):
                print(f"    [{i}] {sm}")
            print(
                "  Use --semantic-model <path> to specify which one to use."
            )

    print(f"Scaffolded PBIP project: {root}")
    print(f"  {project_name}.pbip")
    print(f"  .gitignore")
    print(f"  {project_name}.SemanticModel/")
    print(f"    .platform")
    print(f"    definition.pbism (version 4.2, TMDL format)")
    print(f"    .pbi/editorSettings.json")
    print(f"    definition/cultures/en-US.tmdl")
    print(f"    definition/ (ready for TMDL files)")
    print(f"  {project_name}.Report/")
    print(f"    .platform")
    print(f"    definition.pbir (version 4.0, PBIR format)")
    print(f"    definition/report.json")
    print(f"    definition/version.json")
    print(f"    definition/pages/pages.json")
    print(f"    definition/pages/{page_id}/page.json")
    print(f"    definition/pages/{page_id}/visuals/ (ready for visual.json files)")

    return root


def main():
    parser = argparse.ArgumentParser(description="Scaffold a PBIP directory structure")
    parser.add_argument("project_name", help="Name of the PBIP project")
    parser.add_argument("--output", "-o", default="generated-reports", help="Output directory (default: generated-reports)")
    parser.add_argument(
        "--repo-root",
        default=None,
        help="Repository root to search for existing .pbip projects and SemanticModel folders",
    )
    parser.add_argument(
        "--semantic-model",
        default=None,
        help="Path to an existing SemanticModel folder to copy into the output",
    )
    args = parser.parse_args()

    sm_path = args.semantic_model
    if sm_path and not os.path.isdir(sm_path):
        print(f"Error: {sm_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    scaffold(args.project_name, args.output, repo_root=args.repo_root, semantic_model_path=sm_path)


if __name__ == "__main__":
    main()
