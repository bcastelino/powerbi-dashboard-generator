---
name: project-packager
description: Scaffolds a complete Power BI Desktop Project (PBIP) directory structure, assembles TMDL and report artifacts, validates the project integrity, and creates a distributable zip archive. Use this skill when all semantic model and report files are ready and need to be packaged into a valid PBIP. This is Stage 4 of the query-to-pbip pipeline.
---

# Project Packager

Scaffold, assemble, validate, and zip a Power BI Desktop Project (PBIP). This skill takes the TMDL files from the semantic mapper and the report files from the visual generator and packages them into a complete PBIP directory structure that can be opened in Power BI Desktop.

## When to Use This Skill

- Assembling TMDL and report files into a PBIP directory structure
- Creating pointer files (.pbip, .pbism, .pbir) and .platform files with correct cross-references
- Validating that all required PBIP files exist and references are consistent
- Zipping a PBIP project for distribution
- Packaging artifacts as part of the query-to-pbip pipeline (Stage 4)

## Inputs

- **TMDL files** — From Stage 1 (database.tmdl, model.tmdl, relationships.tmdl, tables/*.tmdl)
- **Report files** — From Stage 3 (visual.json files, one per visual)
- **Project name** — Used for directory and pointer file naming

## Outputs

- Complete PBIP directory structure on disk
- Zipped PBIP archive (`.zip`) ready for distribution

## PBIP Directory Structure

The official Microsoft PBIP format (with TMDL semantic model and PBIR report format):

```
<ProjectName>/
├── <ProjectName>.pbip                              # Project entry point
├── .gitignore                                      # Excludes local settings and cache
├── <ProjectName>.SemanticModel/
│   ├── .platform                                   # Fabric Git integration (type: SemanticModel)
│   ├── definition.pbism                             # Semantic model pointer (version 4.2 for TMDL)
│   ├── diagramLayout.json                           # Model diagram layout (optional)
│   ├── .pbi/
│   │   └── editorSettings.json                      # Editor configuration
│   └── definition/
│       ├── database.tmdl                            # Database name + compatibility level
│       ├── model.tmdl                               # Model configuration
│       ├── relationships.tmdl                       # Table relationships
│       ├── cultures/
│       │   └── en-US.tmdl                           # Culture/locale definition
│       └── tables/
│           ├── fact_sales.tmdl
│           ├── dim_customer.tmdl
│           └── ...
└── <ProjectName>.Report/
    ├── .platform                                   # Fabric Git integration (type: Report)
    ├── definition.pbir                              # Report pointer (version 4.0, references SemanticModel)
    ├── StaticResources/
    │   └── SharedResources/
    │       └── BaseThemes/
    │           └── CY25SU11.json                    # Default Power BI theme
    └── definition/
        ├── report.json                              # Report-level configuration (schema 3.1.0)
        ├── version.json                             # Report format version metadata
        └── pages/
            ├── pages.json                           # Page ordering and active page
            └── <pageId>/                            # 20-char hex page identifier
                ├── page.json                        # Page definition (schema 2.0.0)
                └── visuals/
                    ├── <visualId>/                  # 20-char hex visual identifier
                    │   └── visual.json              # Visual definition (schema 2.5.0)
                    └── <visualId>/
                        └── visual.json
```

## Packaging Workflow

### Step 1: Create Directory Structure

Create the full directory hierarchy. Use `scripts/scaffold_pbip.py` from the query-to-pbip skill:

```bash
python scaffold_pbip.py <ProjectName> --output <output-dir>
```

This generates all directories, pointer files, `.platform` files, and stub report files.

### Step 2: Generate Pointer Files

**`<ProjectName>.pbip`** — Project entry point:
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/pbip/pbipProperties/1.0.0/schema.json",
  "version": "1.0",
  "artifacts": [
    {
      "report": {
        "path": "<ProjectName>.Report"
      }
    }
  ],
  "settings": {
    "enableAutoRecovery": true
  }
}
```

**`definition.pbism`** — Semantic model pointer (in `<ProjectName>.SemanticModel/`):
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
  "version": "4.2",
  "settings": {}
}
```

Version `4.2` indicates the semantic model definition is stored as TMDL in the `definition/` folder.

**`definition.pbir`** — Report pointer (in `<ProjectName>.Report/`):
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byPath": {
      "path": "../<ProjectName>.SemanticModel"
    }
  }
}
```

Version `4.0` indicates the report definition is stored in PBIR format in the `definition/` folder.

### Step 3: Generate .platform Files

Each item folder (SemanticModel and Report) requires a `.platform` file for Fabric Git integration:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
  "metadata": {
    "type": "SemanticModel",
    "displayName": "<ProjectName>"
  },
  "config": {
    "version": "2.0",
    "logicalId": "<generated-guid>"
  }
}
```

The `type` field is `"SemanticModel"` or `"Report"` depending on the folder. The `logicalId` is a unique GUID.

### Step 4: Generate Report Definition Files

**`definition/report.json`** — Report configuration:
```json
{
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
    "useStylableVisualContainerHeader": true,
    "exportDataMode": "AllowSummarized",
    "defaultDrillFilterOtherVisuals": true,
    "allowChangeFilterTypes": true,
    "useEnhancedTooltips": true,
    "useDefaultAggregateDisplayName": true
  }
}
```

**`definition/version.json`**:
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
  "version": "2.0.0"
}
```

**`definition/pages/pages.json`** — Page ordering:
```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
  "pageOrder": ["<pageId>"],
  "activePageName": "<pageId>"
}
```

### Step 5: Place Artifact Files

Copy files from previous pipeline stages into the correct locations:

| Source | Destination |
|---|---|
| `database.tmdl` | `<ProjectName>.SemanticModel/definition/database.tmdl` |
| `model.tmdl` | `<ProjectName>.SemanticModel/definition/model.tmdl` |
| `relationships.tmdl` | `<ProjectName>.SemanticModel/definition/relationships.tmdl` |
| `tables/*.tmdl` | `<ProjectName>.SemanticModel/definition/tables/` |
| `visual.json` (per visual) | `<ProjectName>.Report/definition/pages/<pageId>/visuals/<visualId>/visual.json` |

### Step 6: Validate the Structure

Run validation to ensure project integrity:

```bash
python package_pbip.py <ProjectDir> --validate-only
```

Validation checks:
1. **File existence** — `.pbip`, `.pbism`, `.pbir`, `database.tmdl`, `model.tmdl` all exist
2. **Pointer consistency** — `.pbir` references the correct `.SemanticModel` path
3. **PBISM version** — Must be `4.x` for TMDL format
4. **Platform files** — `.platform` exists in both SemanticModel and Report
5. **Report definition** — `definition/report.json` and `definition/version.json` exist
6. **Pages** — `pages.json` exists, at least one page directory with `page.json`
7. **Visuals** — Each visual directory contains `visual.json`
8. **Table files** — At least one `.tmdl` file in `tables/`

### Step 7: Create Zip Archive

Package the validated project into a zip archive:

```bash
python package_pbip.py <ProjectDir> --output <ProjectName>.zip
```

The zip excludes `.pbi/localSettings.json` and `.pbi/cache.abf` (local-only files).

## File Format Requirements

| File Type | Encoding | Indentation | Line Endings |
|---|---|---|---|
| `.tmdl` | UTF-8 (no BOM) | Tab | LF |
| `.json` | UTF-8 (no BOM) | 2 spaces | LF |
| `.pbip`, `.pbism`, `.pbir`, `.platform` | UTF-8 (no BOM) | 2 spaces | LF |

## Validation Checklist

Before delivering the PBIP:

1. **Project file exists** — `<ProjectName>.pbip` is present in root
2. **`.gitignore` exists** — Excludes `.pbi/localSettings.json` and `.pbi/cache.abf`
3. **Semantic model complete** — `.platform`, `definition.pbism` (v4.2), `database.tmdl`, `model.tmdl` all exist
4. **Tables present** — At least one `.tmdl` file in `tables/`
5. **Culture defined** — `cultures/en-US.tmdl` exists
6. **Relationships file exists** — `relationships.tmdl` is present (even if empty)
7. **Report complete** — `.platform`, `definition.pbir` (v4.0), `definition/report.json`, `definition/version.json`
8. **Pages configured** — `pages.json` with at least one page ID, matching page directory with `page.json`
9. **Visuals present** — At least one `visual.json` in a visual subdirectory
10. **Pointer paths correct** — `.pbir` → `../<ProjectName>.SemanticModel`

## Error Handling

| Error | Resolution |
|---|---|
| Missing TMDL files from Stage 1 | Report which files are missing; do not create zip |
| Missing visual.json files from Stage 3 | Report which files are missing; do not create zip |
| Pointer path mismatch | Auto-correct the path based on project name |
| Empty tables directory | Warn but allow packaging (model may have no dimensions) |
| Missing .platform files | Generate them with new GUIDs |
| PBISM version mismatch | Update to version 4.2 for TMDL format |

## Opening the PBIP

To use the generated PBIP:

1. Extract the zip archive
2. Open `<ProjectName>.pbip` in Power BI Desktop (June 2023 or later with PBIP preview enabled)
3. Power BI will load the semantic model and report definition
4. If the Databricks connection is configured, visuals will render with live data
