---
name: query-to-pbip
description: Orchestrates the end-to-end conversion of a Databricks Genie Query into a Power BI Desktop Project (PBIP) with visuals. Use this skill when transforming a Genie SQL query or YAML metric view into a complete, openable Power BI project containing a semantic model (TMDL) and report visuals (PBIR). It coordinates four sub-skills in sequence — semantic-mapper, visual-selector, visual-generator, and project-packager — to produce a zipped PBIP artifact.
---

# Query To Pbip

Orchestrate the conversion of a Databricks Genie Query into a complete Power BI Desktop Project (PBIP). This skill acts as a pipeline controller, invoking four sub-skills in sequence to translate query semantics into a TMDL model, select an appropriate visual type, generate the visual JSON, and scaffold the final PBIP package.

## When to Use This Skill

- Converting a Genie SQL query or YAML metric view into a Power BI visual
- Generating a complete PBIP project from a natural language query result
- Producing a downloadable `.pbip` artifact from Genie output
- Automating the end-to-end pipeline from query to Power BI report

## Pipeline Overview

The orchestration follows a strict four-stage pipeline. Each stage produces an artifact consumed by the next:

```
┌─────────────────┐     ┌──────────────────┐     ┌───────────────────┐     ┌───────────────────┐
│ semantic-mapper  │────▶│ visual-selector   │────▶│ visual-generator  │────▶│ project-packager  │
│                  │     │                   │     │                   │     │                   │
│ Genie YAML ──▶  │     │ TMDL + SQL ──▶    │     │ Visual Type ──▶   │     │ All artifacts ──▶ │
│ TMDL Model      │     │ Visual Type       │     │ visual.json       │     │ Zipped PBIP       │
└─────────────────┘     └──────────────────┘     └───────────────────┘     └───────────────────┘
```

**Input:** A Genie Query — either as raw SQL, a YAML metric view snippet, or the full `genie-metric-view.yaml` file.

**Output:** A zipped PBIP directory ready to open in Power BI Desktop.

## Stage 1: Semantic Mapper

**Purpose:** Translate the Genie SQL (YAML) into a Power BI TMDL semantic model.

**Sub-skill:** `semantic-mapper`

Convert the Databricks Genie YAML metric view (or a subset relevant to the query) into TMDL format, applying the same conversion patterns defined in the `yaml-to-tmdl-converter` skill.

### Inputs

- Genie YAML metric view (full file or relevant subset)
- Query context: which measures and dimensions the query references
- SQL aliases from the query output that are not native semantic-model fields (derived fields)

### Process

1. **Parse the Genie Query** — Identify the measures and dimensions referenced in the query.
2. **Extract relevant YAML** — From the full `genie-metric-view.yaml`, extract only the source, joins, dimensions, and measures that the query touches.
3. **Build a Derived Field Registry** — For any `SELECT ... AS <alias>` field not already in the model, capture alias name, SQL expression, source tables, inferred kind (`dimension`/`measure`), and target materialization (`calculatedColumn`/`measure`).
4. **Convert to TMDL** — Apply the YAML-to-TMDL conversion workflow:
   - Extract source table as the fact table
   - Convert joins to table definitions and relationships
   - Choose the correct role-playing date strategy: separate active date tables when multiple date roles must filter visuals simultaneously, otherwise inactive alternate relationships with `USERELATIONSHIP`
   - Convert SQL measures to DAX measures
   - Materialize derived aliases as calculated columns or measures before visual generation
   - Materialize data-anchored rolling-window helper measures when the request is for the latest N periods in the data
   - Convert format objects to TMDL format strings
   - Generate M-Code partitions for Databricks connectivity
   - Add lineage tags (GUIDs) to every object

### Outputs

- `model.tmdl` — Model-level configuration
- `database.tmdl` — Database name and compatibility level
- `relationships.tmdl` — All table relationships
- `tables/<TableName>.tmdl` — One file per table (fact + dimensions)

### Conversion Quick Reference

| YAML Element | TMDL Output |
|---|---|
| `source:` | Fact table with partition |
| `joins:` with `using:` | Table + relationship (same key) |
| `joins:` with `on:` | Table + relationship (different keys) |
| `measures:` with `SUM(col)` | `measure = SUM(table[col])` |
| `measures:` with `COUNT(DISTINCT col)` | `measure = DISTINCTCOUNT(table[col])` |
| `measures:` with `a / NULLIF(b, 0)` | `measure = DIVIDE(a, b)` |
| `format: { type: currency }` | `formatString: $#,0.00` + annotation |
| `format: { type: percentage }` | `formatString: 0.0%` |
| `window:` (rolling) | `CALCULATE` with `DATESINPERIOD` |

For complete conversion patterns, refer to `references/conversion-patterns.md`.

### Example

**Input (YAML subset):**

```yaml
source: wl_internal.olist_ecommerce.fact_sales
joins:
  - name: dim_customer
    source: wl_internal.olist_ecommerce.dim_customer
    using:
      - customer_key
measures:
  - name: Total Revenue (GMV)
    expr: SUM(total_value)
    format:
      type: currency
      currency_code: USD
```

**Output (fact_sales.tmdl excerpt):**

```tmdl
table fact_sales
    lineageTag: <generated-guid>

    measure 'Total Revenue (GMV)' = SUM(fact_sales[total_value])
        formatString: $#,0.00
        lineageTag: <generated-guid>

    partition fact_sales = m
        mode: directQuery
        source =
                let
                    Source = DatabricksMultiCloud.Catalogs(...),
                    ...
                in
                    fact_sales_Table
```

## Stage 2: Visual Selector

**Purpose:** Determine the best Power BI visual type based on the query's data profile.

**Sub-skill:** `visual-selector`

Analyze the measures and dimensions extracted in Stage 1 to recommend the most appropriate visual type.

### Inputs

- List of measures from Stage 1 (names, data types, format types)
- List of dimensions from Stage 1 (names, data types, cardinality hints)
- Original query intent (e.g., "show revenue by state", "compare monthly trends")

### Selection Rules

Apply the following decision tree to select the visual type:

```
START
  |
  +-- Single measure, no dimensions ------------------> cardVisual
  |
  +-- Single measure, 1 categorical dimension
  |   +-- Dimension is temporal (date/month/year) ----> lineChart
  |   +-- Dimension is nominal (state/category) ------> columnChart
  |
  +-- Single measure, 1 geographic dimension ----------> map
  |
  +-- Multiple measures, no dimensions ----------------> cardVisual (multi-card)
  |
  +-- Multiple measures, 1+ dimensions
  |   +-- Dimension is temporal -----------------------> lineChart
  |   +-- Comparison intent ---------------------------> clusteredBarChart
  |   +-- Default -------------------------------------> tableEx
  |
  +-- 1 measure, 2+ dimensions
  |   +-- Both categorical ----------------------------> matrix
  |   +-- One temporal, one categorical ---------------> lineChart (with series)
  |
  +-- Fallback ----------------------------------------> tableEx
```

### Dimension Classification

| Indicator | Classification | Examples |
|---|---|---|
| Column name contains `date`, `month`, `year`, `quarter`, `time` | Temporal | `order_date`, `Month`, `Year` |
| Column name contains `state`, `city`, `country`, `region`, `zip` | Geographic | `customer_state`, `Region` |
| Column references `dim_date`, `dim_date_delivery`, or another role-playing date table | Temporal | Any date-role column |
| All other columns | Nominal/Categorical | `category_name`, `seller_id` |

### Outputs

- Selected `visualType` string (e.g., `cardVisual`, `clusteredColumnChart`, `lineChart`, `tableEx`, `pivotTable`, `slicer`)
- Query bucket mapping (which fields go into which buckets like Category, Y, Values, Series)
- Recommended page layout position

### Query Bucket Mapping by Visual Type

| Visual Type | Buckets | What Goes Where |
|---|---|---|
| `cardVisual` | `Data` | Single measure |
| `clusteredColumnChart` | `Category`, `Y`, `Series` | Dimension -> Category, Measure -> Y, Derived categorical grouping -> Series |
| `lineChart` | `Category`, `Y`, `Series` | Time -> Category, Measure -> Y, Optional grouping -> Series |
| `tableEx` | `Values` | All dimensions and measures |
| `pivotTable` | `Rows`, `Columns`, `Values` | Dim1 -> Rows, Dim2 -> Columns, Measures -> Values |
| `slicer` | `Values` | Single dimension column |
| `clusteredBarChart` | `Category`, `Y`, `Series` | Dimension -> Category, Measures -> Y, Derived categorical grouping -> Series |
| `filledMap` | `Category`, `Size` | Geo dimension -> Category, Measure -> Size |

If a derived categorical alias exists (for example `Top Flag`), default to placing it in `Series` for supported chart visuals so Power BI legend/color segmentation is preserved.

## Stage 3: Visual Generator

**Purpose:** Build individual `visual.json` files in PBIR format, where each visual is a separate file in its own directory.

**Sub-skill:** `visual-generator`

Take the selected visual type and field mappings from Stage 2 and produce all report definition files in PBIR format.

### Inputs

- `visualType` from Stage 2 (e.g., `cardVisual`, `clusteredColumnChart`, `lineChart`)
- Query bucket mapping from Stage 2
- Table and measure names from Stage 1
- Page layout preferences (defaults: 1280x720, FitToPage)

### Process

1. **Load the visual template** — Select the appropriate template from `assets/visual-templates/` based on the visual type.
2. **Populate field references** — Replace template placeholders with actual table names, column names, and measure names using the semantic query format. Include `nativeQueryRef` (column/measure name without table prefix).
3. **Set positioning** — Calculate the visual position within the page layout. For single visuals, center on the page. For dashboards with multiple visuals, apply the layout grid from `references/layout-patterns.md`.
4. **Write each visual as a separate file** — Each visual gets its own directory: `definition/pages/<pageId>/visuals/<visualId>/visual.json`
5. **Assemble page.json** — Page definition (no embedded visuals — visuals are separate files in PBIR format).
6. **Generate report definition files** — `definition/report.json`, `definition/version.json`, `definition/pages/pages.json`

### Semantic Query Field Format

**Column reference:**

```json
{
  "field": {
    "Column": {
      "Expression": { "SourceRef": { "Entity": "<TableName>" } },
      "Property": "<ColumnName>"
    }
  },
  "queryRef": "<TableName>.<ColumnName>",
  "nativeQueryRef": "<ColumnName>",
  "active": true
}
```

**Measure reference:**

```json
{
  "field": {
    "Measure": {
      "Expression": { "SourceRef": { "Entity": "<FactTableName>" } },
      "Property": "<MeasureName>"
    }
  },
  "queryRef": "<FactTableName>.<MeasureName>",
  "nativeQueryRef": "<MeasureName>"
}
```

### Outputs

| File | Location | Schema Version |
|---|---|---|
| `visual.json` (per visual) | `definition/pages/<pageId>/visuals/<visualId>/` | visualContainer/2.5.0 |
| `page.json` | `definition/pages/<pageId>/` | page/2.0.0 |
| `pages.json` | `definition/pages/` | pagesMetadata/1.0.0 |
| `report.json` | `definition/` | report/3.1.0 |
| `version.json` | `definition/` | versionMetadata/1.0.0 |
| `definition.pbir` | `<ProjectName>.Report/` | definitionProperties/2.0.0 |

### Visual Template Usage

Templates are stored in `assets/visual-templates/`. Each template uses schema version 2.5.0 with `{{placeholder}}` markers:

| Template | PBIR Visual Type | Placeholders |
|---|---|---|
| `cardVisual.json` | `cardVisual` | `{{VisualName}}`, `{{MeasureTable}}`, `{{MeasureName}}` |
| `clusteredColumnChart.json` | `clusteredColumnChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}`, `{{SeriesTable}}`, `{{SeriesColumn}}` |
| `clusteredBarChart.json` | `clusteredBarChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}`, `{{SeriesTable}}`, `{{SeriesColumn}}` |
| `lineChart.json` | `lineChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}` |
| `tableEx.json` | `tableEx` | `{{VisualName}}`, `{{Columns}}` |
| `slicer.json` | `slicer` | `{{VisualName}}`, `{{SlicerTable}}`, `{{SlicerColumn}}` |

To use a template:

1. Read the template file from `assets/visual-templates/`
2. Replace all `{{placeholder}}` values with actual field names from Stage 1 and Stage 2
3. Generate a unique 20-char hex identifier for `{{VisualName}}` (e.g., `uuid.uuid4().hex[:20]`)
4. Set the position coordinates based on the layout
5. Write each visual to its own directory: `visuals/<visualId>/visual.json`

## Stage 4: Project Packager

**Purpose:** Scaffold the complete PBIP directory structure per the official Microsoft PBIP format and prepare it for use.

**Sub-skill:** `project-packager`

Assemble all artifacts from the previous stages into a valid PBIP directory structure with TMDL semantic model and PBIR report format.

### Inputs

- TMDL files from Stage 1 (model, database, relationships, tables)
- Report files from Stage 3 (visual.json files, page.json, report.json, pages.json, version.json, definition.pbir)
- Project name (derived from the query or specified by the user)
- Repository root path (optional — used to discover existing `.pbip` projects)
- Explicit SemanticModel path (optional — used when multiple exist)

### Process

0. **Check for existing PBIP projects** — **Always** search the repository for existing `.pbip` projects and `*.SemanticModel` folders before creating files from scratch. If an existing `<Name>.SemanticModel` folder is found, copy its **entire** contents (including `TMDLScripts/`, `definition/`, `definition.pbism`, `diagramLayout.json`, `.platform`, etc.) into the output. If multiple `SemanticModel` folders are found, prompt the user to confirm which one to use. **You must always pass `--repo-root`** when running `scaffold_pbip.py` so that existing SemanticModel content is discovered and copied. Use `--semantic-model <path>` when you need to target a specific folder.

   **Critical: Do NOT remove any tables, models, relationships, or definition files from the copied SemanticModel** — even if they are not directly referenced by the current visual or query. The complete SemanticModel must remain intact. Removing unused tables breaks `ref table` declarations in `model.tmdl`, removing relationships breaks foreign key integrity, and Power BI Desktop validates the entire model on load. Only **add** new report files — never delete or modify existing SemanticModel content.
1. **Create directory structure** — Scaffold the PBIP folder hierarchy:

   ```
   <ProjectName>/
   ├── <ProjectName>.pbip                              # Project entry point
   ├── .gitignore                                      # Excludes local settings and cache
   ├── <ProjectName>.SemanticModel/
   │   ├── .platform                                   # Fabric Git integration (type: SemanticModel)
   │   ├── definition.pbism                             # Semantic model pointer (version 4.2 for TMDL)
   │   ├── TMDLScripts/                                 # Consolidated TMDL (generated or copied)
   │   │   ├── power-bi-semantic-model.tmdl              # Single-file createOrReplace TMDL
   │   │   └── .pbi/
   │   │       └── tmdlScripts.json                      # TMDLScripts metadata
   │   ├── diagramLayout.json                           # Diagram layout (copied from existing project if available)
   │   ├── .pbi/
   │   │   └── editorSettings.json                      # Editor configuration
   │   └── definition/
   │       ├── database.tmdl
   │       ├── model.tmdl
   │       ├── relationships.tmdl
   │       ├── cultures/
   │       │   └── en-US.tmdl                           # Culture/locale definition
   │       └── tables/
   │           ├── fact_sales.tmdl
   │           ├── dim_customer.tmdl
   │           └── ...
   └── <ProjectName>.Report/
       ├── .platform                                   # Fabric Git integration (type: Report)
       ├── definition.pbir                              # Report pointer (version 4.0, PBIR format)
       ├── StaticResources/
       │   └── SharedResources/
       │       └── BaseThemes/
       │           └── CY25SU11.json                    # Default Power BI theme
       └── definition/
           ├── report.json                              # Report config (schema 3.1.0)
           ├── version.json                             # Report format version
           └── pages/
               ├── pages.json                           # Page ordering and active page
               └── <pageId>/                            # 20-char hex page identifier
                   ├── page.json                        # Page definition (schema 2.0.0)
                   └── visuals/
                       ├── <visualId>/
                       │   └── visual.json              # Visual definition (schema 2.5.0)
                       └── <visualId>/
                           └── visual.json
   ```

2. **Generate pointer files with correct schemas:**
   - `<ProjectName>.pbip` — Schema: `pbipProperties/1.0.0`, version `1.0`
   - `definition.pbism` — Schema: `semanticModel/definitionProperties/1.0.0`, version `4.2` (TMDL)
   - `definition.pbir` — Schema: `report/definitionProperties/2.0.0`, version `4.0` (PBIR)
3. **Generate .platform files** — Fabric Git integration metadata for both SemanticModel and Report
4. **Write TMDL files** — Place all semantic model files from Stage 1
5. **Write report files** — Place all report files from Stage 3 (individual visual.json files in their directories)
6. **Validate structure** — Verify all required files exist and references are consistent
7. **Package** — Create a zip archive of the PBIP directory (excluding `.pbi/localSettings.json` and `.pbi/cache.abf`)

### Pointer File Templates

**`<ProjectName>.pbip`:**

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

**`definition.pbism`** (version 4.2 = TMDL format in `definition/` folder):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/semanticModel/definitionProperties/1.0.0/schema.json",
  "version": "4.2",
  "settings": {}
}
```

**`definition.pbir`** (version 4.0 = PBIR format in `definition/` folder):

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

**`.platform`** (one in each item folder):

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

### Outputs

- Complete PBIP directory structure
- Zipped PBIP archive (`.zip`)

### File Format Requirements

- All text files: UTF-8 without BOM
- JSON files: 2-space indentation
- TMDL files: Tab indentation
- Line endings: LF (Unix-style)

## End-to-End Execution Workflow

To execute the full pipeline for a given Genie query:

### Step 1: Receive and Parse the Query

Identify what the user is asking for. The input can be:

- A natural language question (e.g., "Show me revenue by state")
- A Genie SQL query
- A YAML metric view file or snippet

Extract the referenced measures and dimensions from the input.

### Step 2: Run the Semantic Mapper (Stage 1)

1. Load the Genie YAML metric view (from `databricks-genie-metric-view/genie-metric-view.yaml` or a provided file)
2. Filter to only the measures, dimensions, and joins relevant to the query
3. Build a Derived Field Registry for SQL aliases not present in the model
4. Materialize derived aliases into TMDL as calculated columns or measures
5. Apply the YAML-to-TMDL conversion following the patterns in `references/conversion-patterns.md`
6. Generate all TMDL files (model, database, relationships, tables)

### Step 3: Run the Visual Selector (Stage 2)

1. Analyze the measures and dimensions from Step 2
2. Classify each dimension (temporal, geographic, nominal)
3. Apply the visual selection decision tree
4. Produce the visual type and query bucket mapping

If a derived categorical alias is available from Stage 1, map it to `Series` for chart visuals by default to render legend-based color splits.

### Step 4: Run the Visual Generator (Stage 3)

1. Load the appropriate visual template from `assets/visual-templates/`
2. Replace placeholders with actual table/column/measure names (include `nativeQueryRef`)
3. **Populate date range filter placeholders** — If the Genie query contains date-level filters:
   - For **absolute** date ranges (e.g., `FROM '2017-01-01' TO '2017-12-31'`): use the literal dates directly.
   - For **current-date-relative** ranges (e.g., "last 12 months", "past 6 months", "last 90 days"): emit a native PBIR `RelativeDate` filter using `Now` / `DateAdd`, following the same shape as the reference `generated-reports/DeliveryDaysTrends/.../visual.json`.
   - For **data-anchored** ranges (e.g., "latest 12 months in the data", or historical datasets where the latest row is older than today): do not use native `RelativeDate`; instead, bind a Stage 1 helper measure/flag and add a standard visual filter requiring that helper to evaluate to `1`.
   - Set the date entity/property to the correct semantic timeline (`dim_date.date` for purchase/order trends, `dim_date_delivery.date` for delivery trends).
4. Write each visual as a separate `visual.json` file in `definition/pages/<pageId>/visuals/<visualId>/`
5. Generate `page.json` (page container without embedded visuals — PBIR format)
6. Generate `pages.json`, `report.json`, `version.json`, and `definition.pbir`

### Step 5: Run the Project Packager (Stage 4)

1. Check for existing `.pbip` projects in the repository (search for `*.SemanticModel` folders)
2. Scaffold the PBIP directory — **always** pass the repo root:

   ```
   python scripts/scaffold_pbip.py <ProjectName> --repo-root <repo-root-path>
   ```

   - This automatically discovers and copies existing SemanticModel contents (including `TMDLScripts/`, `definition/`, `diagramLayout.json`, etc.) into the output
   - If multiple SemanticModel folders exist, use `--semantic-model <path>` to specify which one
   - **Never** omit `--repo-root` — without it, the existing SemanticModel will not be copied
3. Write all TMDL files from Step 2 into `<ProjectName>.SemanticModel/definition/`
   - **Do NOT remove** any existing tables, models, relationships, or definition files from the copied SemanticModel
4. Write all report files from Step 4 into `<ProjectName>.Report/definition/`
5. Generate pointer files (`.pbip`, `.pbism` v4.2, `.pbir` v4.0) and `.platform` files
6. **Generate consolidated TMDLScripts** — After all TMDL files are written to `definition/`, run:

   ```
   python scripts/generate_tmdl_scripts.py <ProjectName>/<ProjectName>.SemanticModel
   ```

   This reads the split files from `definition/` (model.tmdl, tables/*.tmdl, relationships.tmdl, cultures/*.tmdl) and produces a single `TMDLScripts/power-bi-semantic-model.tmdl` in the `createOrReplace` format. The `TMDLScripts/.pbi/tmdlScripts.json` metadata file is created during scaffolding.
7. Validate the structure (using `scripts/package_pbip.py --validate-only`)
8. Zip the project directory (excluding `.pbi/localSettings.json` and `.pbi/cache.abf`)

### Step 6: Deliver the Result

Provide the user with:

- The zipped PBIP file
- A summary of what was generated (tables, measures, visual type)
- Instructions to open in Power BI Desktop

## Error Handling

| Stage | Common Error | Resolution |
|---|---|---|
| Semantic Mapper | Unknown DAX conversion for SQL function | Fall back to inline SQL comment with TODO marker |
| Semantic Mapper | Missing join definition | Skip the dimension, warn the user |
| Visual Selector | Ambiguous query intent | Default to `tableEx` (table visual) |
| Visual Generator | Template placeholder not found | Use generic field reference |
| Project Packager | Invalid directory structure | Re-scaffold from template |
| Project Packager | Missing required files | Report which files are missing |

## Validation Checklist

Before delivering the final PBIP, verify:

1. **Semantic Model Completeness** — All referenced tables, columns, and measures exist in TMDL files
1b. **Measure Syntax** — Every measure uses inline expression syntax (`measure 'Name' = <DAX>`). Measures must NOT contain `displayName`, `dataType`, `sourceColumn`, or `expression =` as separate properties — these are either column-only or invalid TMDL keywords
1c. **Calculated Column Syntax** — Every derived calculated column uses inline DAX expression syntax (`column 'Name' = <DAX expression>`). Calculated columns must NOT contain `sourceColumn:` or `sourceProviderType:` — these are source column properties only and are invalid on calculated columns. The keyword `calculatedColumn` must never appear as a TMDL property name. **DirectQuery restriction:** calculated column DAX must NOT use iterator functions (`RANKX`, `SUMX`, `AVERAGEX`, `COUNTX`, `MAXX`, `MINX`, `FILTER`, `ADDCOLUMNS`, `SELECTCOLUMNS`). Reference pre-existing source columns instead (e.g., use `table[volume_rank]` not `RANKX(...)`). If no source column exists, convert to a measure.
1d. **Column Properties** — Every source column MUST include `sourceProviderType` and `annotation SummarizationSetBy = Automatic`. `int64` columns must have `formatString: 0`. `double` columns must have `annotation PBI_FormatHint = {"isGeneralNumber":true}`. `dateTime` columns must have appropriate `formatString` (`Long Date` or `General Date`)
1e. **Model Format** — `model.tmdl` must include `dataAccessOptions` block (with `legacyRedirects` and `returnErrorValuesAsNull`) and `annotation __PBI_TimeIntelligenceEnabled = 1`. Must NOT include `discourageImplicitMeasures`
1f. **Table Annotations** — Every table must end with `annotation PBI_ResultType = Table`
2. **Relationship Integrity**— All joins from YAML are converted to relationships; relationships use the GUID as name (NOT as `lineageTag`); each has `annotation PBI_IsFromSource = FS`
2b. **Role-Playing Date Strategy** — Multiple simultaneously active date roles use separate role-playing date tables; inactive alternate relationships are used only when the alternate role is measure-only
3. **Visual Binding** — The visual's query references match actual table/measure names in the TMDL
3b. **Timeline Alignment** — Temporal visuals and date filters use the correct date role (`dim_date`, `dim_date_delivery`, etc.) for the requested trend
4. **Pointer Consistency** — `.pbip` -> `.Report`, `.pbir` -> `.SemanticModel` paths are correct
5. **Schema Versions** — `.pbism` version 4.2 (TMDL), `.pbir` version 4.0 (PBIR), visual schema 2.5.0
6. **Platform Files** — `.platform` exists in both SemanticModel and Report folders
7. **Report Definition** — `definition/report.json`, `definition/version.json`, `definition/pages/pages.json` all present
8. **File Format** — UTF-8 encoding, correct indentation (tabs for TMDL, 2-space for JSON)
9. **GUID Uniqueness** — All lineage tags are unique across the project
10. **Relationship Format** — Relationships do NOT contain `lineageTag` (causes `UnknownKeyword` error); the GUID is the relationship name
11. **SemanticModel Copy** — If an existing SemanticModel was found, verify `TMDLScripts/` and other contents are present in the output
11b. **TMDLScripts** — `TMDLScripts/power-bi-semantic-model.tmdl` must exist and contain the consolidated `createOrReplace` TMDL combining all tables, relationships, and culture info. `TMDLScripts/.pbi/tmdlScripts.json` must exist with version, tabOrder, and defaultTab
12. **SemanticModel Integrity** — No tables, models, relationships, or definition files were removed from the copied SemanticModel
13. **sortDefinition** — Every visual.json includes a `sortDefinition` in the `visual->query` block for proper default sorting
14. **Last-N-Month Filter Mode** — Current-date rolling windows use native PBIR `RelativeDate`; data-anchored rolling windows use helper measures/flags rather than `Now`

## Resources

### references/

- `conversion-patterns.md` — Complete YAML-to-TMDL and DAX-to-SQL conversion reference
- `layout-patterns.md` — Page layout grid patterns for multi-visual dashboards
- `visual-selection-rules.md` — Detailed visual selection decision tree with examples

### assets/visual-templates/

- `cardVisual.json` — Card visual (`cardVisual`, schema 2.5.0)
- `columnChart.json` — Column chart (`columnChart`, schema 2.5.0)
- `clusteredColumnChart.json` — Clustered column chart (`clusteredColumnChart`, schema 2.5.0)
- `clusteredBarChart.json` — Clustered bar chart (`clusteredBarChart`, schema 2.5.0)
- `lineChart.json` — Line chart (`lineChart`, schema 2.5.0)
- `tableEx.json` — Table visual (`tableEx`, schema 2.5.0)
- `slicer.json` — Slicer visual (`slicer`, schema 2.5.0)
- `page-template.json` — Base page container (schema 2.0.0)
- `pages-json.json` — Page ordering template (schema 1.0.0)
- `report-json.json` — Report configuration template (schema 3.1.0)
- `version-json.json` — Report format version template

### scripts/

- `scaffold_pbip.py` — Creates the PBIP directory structure and pointer files
- `generate_tmdl_scripts.py` — Generates consolidated `TMDLScripts/power-bi-semantic-model.tmdl` from split `definition/` files
- `package_pbip.py` — Validates and zips the PBIP directory
