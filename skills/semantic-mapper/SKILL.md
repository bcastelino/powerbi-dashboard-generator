---
name: semantic-mapper
description: Translates a data model description into a Power BI TMDL semantic model. Accepts either (a) a Databricks Genie YAML metric view OR (b) a normalized data-model.json produced by data-source-connector. Use this skill whenever a query or data model needs to be converted into TMDL files (model, database, relationships, tables) for use in a Power BI Desktop Project. This is Stage 1 of the query-to-pbip pipeline.
---

# Semantic Mapper

Translate a data model description into a Power BI TMDL semantic model. This skill accepts either a Databricks Genie YAML metric view (legacy path) or a source-agnostic `data-model.json` produced by `data-source-connector` (preferred path for non-Databricks sources), and produces the complete set of TMDL files needed for a Power BI semantic model.

## Input Modes

The skill supports two input formats. Detect which mode to use based on the input artifact:

| Mode | Input Artifact | When To Use |
|---|---|---|
| `yaml` (legacy) | Genie YAML metric view (`genie-metric-view.yaml`) | Databricks Genie workflows where a curated metric view already exists |
| `data-model` (preferred) | `data-model.json` from `data-source-connector` | Any other source: SQL DBs, Snowflake, BigQuery, Excel, CSV, OData, SharePoint, etc. |

### `data-model` Mode Mapping

When the input is `data-model.json`, map its fields directly to the TMDL generation steps below:

| `data-model.json` field | TMDL artifact | Step |
|---|---|---|
| `tables[]` | One file per table in `tables/<TableName>.tmdl` | Step 8 |
| `tables[].columns[]` | `column` blocks inside each table file | Step 8 |
| `tables[].columns[].dataType` + `.sourceProviderType` | TMDL `dataType:` and `sourceProviderType:` properties | Step 8 |
| `tables[].role` (= `fact`) | Owns measures (when measures are user-defined in the Dashboard Plan) | Step 5 |
| `tables[].role` (= `date dimension`) | Tagged with `dataCategory: Time` and used in role-playing logic | Step 4 |
| `relationships[]` | Entries in `relationships.tmdl` | Step 4 |
| `mCodeAdapter.templates[<table>]` | Verbatim body of the `partition <table> = m / source = ...` block | Step 7 |
| `mCodeAdapter.mode` | `mode: directQuery` or `mode: import` on each partition | Step 7 |
| All table names | Listed under `annotation PBI_QueryOrder` and `ref table <name>` in `model.tmdl` | Step 3 |

In `data-model` mode, measures come from the **Dashboard Plan** (from `nlq-dashboard-orchestrator`) rather than from YAML `measures:` blocks. Apply the DAX conversion rules in Step 5 to those measure expressions.

In `data-model` mode, **skip Step 7's M-Code template generation** — instead, copy `mCodeAdapter.templates[<table>]` verbatim into the partition's `source =` block. This keeps the connector responsible for source-specific M-Code while `semantic-mapper` stays source-agnostic.

The YAML path below (Steps 1–9) remains the canonical reference for the underlying TMDL output shape. Both modes converge on the same TMDL artifacts.

---

## When to Use This Skill

- Converting Genie YAML metric views to Power BI TMDL format
- Generating TMDL files from a subset of measures and dimensions referenced in a query
- Producing semantic model artifacts for the query-to-pbip pipeline (Stage 1)
- Creating table, relationship, and measure definitions from YAML source definitions

## Inputs

- **Genie YAML metric view** — Full file or relevant subset containing `source`, `joins`, `dimensions`, and `measures`
- **Query context** (optional) — List of measure and dimension names the query references, used to filter the YAML to only relevant elements
- **Derived query fields** (optional) — SQL `SELECT` aliases not present in YAML (for example: `CASE ... AS band`, `DATE_TRUNC(...) AS Month Bucket`, `SUM(...) / COUNT(...) AS Ratio`). These must be materialized into the semantic model as calculated columns or measures before visual binding.
- **Connection parameters** — Databricks workspace hostname and SQL warehouse ID for M-Code partition generation. These MUST be used in all generated M-Code partitions — never hardcode connection values

## Outputs

The skill produces the following TMDL files:

| File | Purpose |
|---|---|
| `database.tmdl` | Database name and compatibility level |
| `model.tmdl` | Model-level configuration (culture, data source version) |
| `relationships.tmdl` | All table relationships derived from YAML joins |
| `tables/<TableName>.tmdl` | One file per table (fact table + each dimension) |

## Conversion Workflow

### Step 1: Parse and Filter the YAML

Read the YAML metric view and identify the relevant sections:

1. **source** — The fact table's three-part identifier (`catalog.schema.table`)
2. **joins** — Dimension table connections (determines which dimension tables to create)
3. **dimensions** — Column definitions with display names and comments
4. **measures** — SQL expressions to convert to DAX

If a query context is provided, filter **joins** and **measures** to only those referenced by the query. Always include the source (fact table).

If the SQL query includes `SELECT` aliases that are not already available in the semantic model, build a **Derived Field Registry** during parsing. Each derived field entry should include:

- `name` — Alias name from SQL (`Top Flag`, `Revenue Band`, etc.)
- `sqlExpression` — Original SQL expression used for traceability
- `sourceTables` — Tables used in the expression
- `semanticKind` — `dimension` or `measure`
- `materializationType` — `calculatedColumn` or `measure`
- `targetTable` — Table where the artifact should be written in TMDL

Treat this registry as a first-class Stage 1 output: Stage 2 and Stage 3 must only bind visuals to model fields that exist in TMDL (native or derived).

**Important: Do NOT remove any tables, models, relationships, or definition files from the SemanticModel** — even if they are not directly referenced by the current query or visual. When an existing SemanticModel is copied, its complete content must remain intact. Only add or update files — never delete existing SemanticModel content.

**Important: Load ALL columns from each selected table.**When a table is included in the model (whether as the fact table or a dimension from a join), include **every column** from that table in the TMDL file — not just the columns referenced in the query. Power BI needs the complete column set to properly define the DirectQuery connection. Omitting columns causes data incompleteness and can break relationships, measures, and visual bindings.

### Step 2: Generate database.tmdl

```tmdl
database
 compatibilityLevel: 1600
```

**Important:** The `database` declaration has no name argument. Use `compatibilityLevel: 1600` (not `1567` — downgrading from `1600` to `1567` causes a Power BI error: "CompatibilityLevel downgrade is not supported").

### Step 3: Generate model.tmdl

The `model.tmdl` file must include model-level configuration, annotations, and reference declarations for every table and the culture. **Each `ref` declaration must be on its own line** — concatenating them onto a single line causes Power BI Desktop parsing errors.

```tmdl
model Model
 culture: en-US
 defaultPowerBIDataSourceVersion: powerBI_V3
 sourceQueryCulture: en-US
 dataAccessOptions
  legacyRedirects
  returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 1

annotation PBI_QueryOrder = ["<table1>","<table2>","<table3>"]

ref table <table1>
ref table <table2>
ref table <table3>

ref cultureInfo en-US
```

**Critical formatting rules for model.tmdl:**

- Must include `dataAccessOptions` block with `legacyRedirects` and `returnErrorValuesAsNull`
- Must include `annotation __PBI_TimeIntelligenceEnabled = 1`
- Do NOT include `discourageImplicitMeasures` — it is not in the reference model
- Each `ref table <tablename>` MUST be on its own separate line
- `ref cultureInfo en-US` MUST be on its own line (no quotes around `en-US`)
- Table names are unquoted unless they contain spaces or special characters
- Annotations MUST be on separate lines with a blank line before and after
- Use tab characters for indentation under `model Model`
- There MUST be a blank line between the model properties block, annotations, ref table declarations, and ref cultureInfo
- The `annotation PBI_QueryOrder` lists all table names in the model as a JSON array

**Example with three tables (fact_sales, dim_customer, dim_date):**

```tmdl
model Model
 culture: en-US
 defaultPowerBIDataSourceVersion: powerBI_V3
 sourceQueryCulture: en-US
 dataAccessOptions
  legacyRedirects
  returnErrorValuesAsNull

annotation __PBI_TimeIntelligenceEnabled = 1

annotation PBI_QueryOrder = ["dim_customer","dim_date","fact_sales"]

ref table dim_customer
ref table dim_date
ref table fact_sales

ref cultureInfo en-US
```

Ensure every table produced in Step 4 and Step 8 has a corresponding `ref table` line here. The connection parameters (Databricks workspace hostname and SQL warehouse ID) provided as inputs MUST be used in M-Code partitions — never hardcode these values.

### Step 4: Convert Joins to Tables and Relationships

For each join in the YAML, create a dimension table TMDL file and a relationship entry.

**Join with `using:` (same key name on both sides):**

```yaml
joins:
  - name: dim_customer
    source: wl_internal.olist_ecommerce.dim_customer
    using:
      - customer_key
```

Produces relationship:

```tmdl
relationship <guid>
 fromColumn: fact_sales.customer_key
 toColumn: dim_customer.customer_key

 annotation PBI_IsFromSource = FS
```

**Join with `on:` (different key names):**

```yaml
joins:
  - name: dim_date
    source: wl_internal.olist_ecommerce.dim_date
    on:
      purchase_date_key: date_key
```

Produces relationship:

```tmdl
relationship <guid>
 fromColumn: fact_sales.purchase_date_key
 toColumn: dim_date.date_key

 annotation PBI_IsFromSource = FS
```

**Role-playing dimension (aliased join to same source table):**

When two joins reference the same source table with different aliases, choose the relationship strategy based on the intended analytical behavior:

- If both date roles must filter visuals simultaneously, generate a separate role-playing table in TMDL (for example `dim_date_delivery`) and keep both relationships active against different tables.
- If the alternate date role is only needed inside a measure, keep a single shared date table and mark the alternate relationship as inactive for later use with `USERELATIONSHIP`.

**Active role-playing table example:**

```tmdl
relationship <guid>
 fromColumn: fact_sales.purchase_date_key
 toColumn: dim_date.date_key

 annotation PBI_IsFromSource = FS

relationship <guid>
 fromColumn: fact_sales.delivered_date_key
 toColumn: dim_date_delivery.date_key

 annotation PBI_IsFromSource = FS
```

**Inactive-relationship fallback example:**

```tmdl
relationship <guid>
 isActive: false
 fromColumn: fact_sales.delivered_date_key
 toColumn: dim_date.date_key

 annotation PBI_IsFromSource = FS
```

**Critical formatting rules for relationships.tmdl:**

- The `<guid>` is the relationship **name/identifier** — it goes on the `relationship` declaration line, NOT as a `lineageTag` property
- Relationships do **NOT** support a `lineageTag` property — adding one causes a `TMDL Format Error: UnknownKeyword` parsing error
- Each relationship MUST include `annotation PBI_IsFromSource = FS` (with a blank line before it)
- Use tab indentation for properties under the relationship declaration
- Separate each relationship block with a blank line

### Step 5: Convert SQL Measures to DAX

Apply these conversion patterns to each measure's `expr` field:

| SQL Expression | DAX Equivalent |
|---|---|
| `SUM(column)` | `SUM(table[column])` |
| `COUNT(DISTINCT column)` | `DISTINCTCOUNT(table[column])` |
| `COUNT(*)` | `COUNTROWS(table)` |
| `AVG(column)` | `AVERAGE(table[column])` |
| `a / NULLIF(b, 0)` | `DIVIDE(a, b)` |
| `CASE WHEN x THEN a ELSE b END` | `IF(x, a, b)` or `VAR/RETURN` pattern |
| `table.column` | `RELATED('table'[column])` |

**Complex CASE WHEN patterns** should use the VAR/RETURN pattern:

```dax
VAR Promoters = CALCULATE(COUNTROWS('dim_review'), 'dim_review'[review_score] = 5)
VAR Detractors = CALCULATE(COUNTROWS('dim_review'), 'dim_review'[review_score] = 1)
VAR TotalReviews = COUNTROWS('dim_review')
RETURN DIVIDE(Promoters - Detractors, TotalReviews)
```

**Window functions** translate to time intelligence:

```yaml
window:
  order: order_date
  range:
    trailing: 7
    frame: day
```

Becomes:

```dax
CALCULATE(
    [Base Measure],
    DATESINPERIOD(dim_date[date], MAX(dim_date[date]), -7, DAY)
)
```

**Data-anchored last-N-month flag (historical datasets):**

When the query intent is "latest N months in the data" rather than "last N months from today", materialize a helper measure or flag in Stage 1 so Stage 3 can filter on it deterministically.

```dax
measure 'Show Last 12 Purchase Months' =
 VAR MaxAvailableDate = MAXX(ALL(fact_sales), RELATED('dim_date'[date]))
 VAR WindowStart = EOMONTH(MaxAvailableDate, -12) + 1
 VAR WindowEnd = EOMONTH(MaxAvailableDate, 0)
 VAR AxisDate = MAX('dim_date'[date])
 RETURN IF(NOT ISBLANK(MaxAvailableDate) && AxisDate >= WindowStart && AxisDate <= WindowEnd, 1, 0)
```

Use the same pattern with the correct role-playing table (`dim_date_delivery`, etc.) when the trend must be anchored to a non-default date role.

### Step 5b: Materialize Derived SQL Aliases

For every SQL alias not already present in the semantic model, create a semantic artifact in TMDL before moving to visual selection.

**Materialization policy:**

- **Row-level expression** (for example `CASE`, `COALESCE`, string/date transforms) -> create a **calculated column** on the owning table.
- **Aggregated expression** (for example `SUM`, `AVG`, `COUNT`, ratio of aggregates) -> create a **measure** on the fact table.
- **Window/rank expression** -> prefer calculated column when deterministic at the row grain **and** the expression only references existing source columns; otherwise create a measure and record a fallback note.

**Generic examples:**

```sql
CASE WHEN volume_rank <= 5 THEN 'Top 5' ELSE 'Non Top 5' END AS Top Flag
```

-> Calculated column (dimension-like, used in legends/series/filters)

```sql
SUM(total_value) / NULLIF(COUNT(DISTINCT order_id), 0) AS AOV
```

-> Measure (value-like, used in Y/Values)

Use the same naming in TMDL as the SQL alias unless there is a direct conflict with an existing field.

**TMDL calculated column template:**

Calculated columns use the inline DAX expression syntax — the `= <DAX expression>` must be on the same line as `column 'Name'`. Do **NOT** include `sourceColumn:` or `sourceProviderType:` — these are source column properties only and are invalid on calculated columns.

**DirectQuery restriction:** Calculated columns on DirectQuery tables cannot use iterator functions (`RANKX`, `SUMX`, `AVERAGEX`, `COUNTX`, `MAXX`, `MINX`, `FILTER`, `ADDCOLUMNS`, `SELECTCOLUMNS`, etc.). Only simple scalar functions and direct column references are allowed. If a rank or window computation is needed, reference the **pre-existing source column** (e.g., `dim_product[volume_rank]`) rather than recomputing with `RANKX`. If no suitable source column exists, convert to a **measure** instead.

```tmdl
column 'Top Flag' = IF(dim_product[volume_rank] <= 5, "Top 5", "Non Top 5")
    dataType: string
    lineageTag: <guid>
    summarizeBy: none

    annotation SummarizationSetBy = Automatic
```

> **Correct:** `IF(dim_product[volume_rank] <= 5, ...)` — references existing source column.
> **Wrong:** `IF(RANKX(ALL(dim_product), dim_product[volume]) <= 5, ...)` — `RANKX` is forbidden in DirectQuery calculated columns.

### Step 6: Convert Format Strings

| YAML Format | TMDL formatString | Annotation |
|---|---|---|
| `type: currency, currency_code: USD` | `$#,0.00` | `PBI_FormatHint = {"currencyCulture":"en-US"}` |
| `type: currency, currency_code: BRL` | `"R$"\ #,0.00` | `PBI_FormatHint = {"currencyCulture":"pt-BR"}` |
| `type: percentage` | `0.0%` | None |
| `type: number, decimal_places: 0` | `#,0` | None |

### Step 7: Generate M-Code Partitions

For each table, generate the M-Code partition connecting to Databricks. Always use the connection parameters provided as inputs — never hardcode hostname or warehouse ID values.

**Critical M-Code formatting rules:**

- **Hostname**: Use the bare hostname WITHOUT `https://` prefix (e.g., `"wl-dbr-dbr-dev-ws-wl.cloud.databricks.com"`, NOT `"https://wl-dbr-dbr-dev-ws-wl.cloud.databricks.com"`)
- **Warehouse ID**: Use the `/sql/1.0/warehouses/<id>` path format (e.g., `"/sql/1.0/warehouses/9d2b45a6a9dda4aa"`)
- **Catalog/Database**: Use empty strings `[Catalog = "", Database = ""]`, NOT `null` values
- **Indentation**: Use tabs, matching the surrounding TMDL indentation

```tmdl
partition <table_name> = m
    mode: directQuery
    source =
            let
                Source = DatabricksMultiCloud.Catalogs("<hostname>", "/sql/1.0/warehouses/<warehouse_id>", [Catalog = "", Database = ""]),
                <catalog>_Database = Source{[Name="<catalog>",Kind="Database"]}[Data],
                <schema>_Schema = <catalog>_Database{[Name="<schema>",Kind="Schema"]}[Data],
                <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
            in
                <table>_Table
```

Where:

- `<hostname>` = Databricks workspace hostname (bare domain, no `https://` prefix)
- `<warehouse_id>` = SQL warehouse ID (just the ID portion, the `/sql/1.0/warehouses/` prefix is added in the template)

Extract the three-part identifier from the YAML `source` field:

- `wl_internal.olist_ecommerce.fact_sales` → catalog=`wl_internal`, schema=`olist_ecommerce`, table=`fact_sales`

### Step 8: Generate Table TMDL Files

Assemble each table file with this structure:

```tmdl
table <TableName>
 lineageTag: <guid>

 measure '<MeasureName>' = <DAX Expression>
  formatString: <format>
  lineageTag: <guid>

 column <column_name>
  dataType: <string|int64|double|dateTime|boolean>
  formatString: <format>
  sourceProviderType: <provider_type>
  lineageTag: <guid>
  summarizeBy: none
  sourceColumn: <column_name>

  annotation SummarizationSetBy = Automatic

 partition <TableName> = m
  mode: directQuery
  source =
    let
        Source = DatabricksMultiCloud.Catalogs("<hostname>", "/sql/1.0/warehouses/<warehouse_id>", [Catalog = "", Database = ""]),
        <catalog>_Database = Source{[Name="<catalog>",Kind="Database"]}[Data],
        <schema>_Schema = <catalog>_Database{[Name="<schema>",Kind="Schema"]}[Data],
        <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
    in
        <table>_Table

 annotation PBI_ResultType = Table
```

Measures belong on the fact table. Columns are distributed to whichever table they originate from (based on the dimension `expr` field prefix like `dim_customer.state`).

Derived artifacts from Step 5b must also be written in this step:

- Add derived calculated columns into the selected `targetTable`.
- Add derived measures into the fact table.
- For derived **calculated columns**: ensure `dataType`, a unique `lineageTag`, `summarizeBy: none`, and `annotation SummarizationSetBy = Automatic` are present. Do NOT include `sourceColumn:` or `sourceProviderType:` on calculated columns.
- For native **source columns**: ensure `dataType`, `sourceProviderType`, `sourceColumn`, a unique `lineageTag`, and `annotation SummarizationSetBy = Automatic` are present.

**Critical: Include ALL columns from each table.** Do not limit columns to only those referenced in the query. Every column in the source table must appear in the TMDL file. Power BI uses DirectQuery, so all columns must be defined for the connection to work correctly. Omitting columns (e.g., including only 4 of 13 columns from `fact_sales`) causes data incompleteness and breaks relationships and measures that depend on the missing columns.

### Step 9: Add Lineage Tags and Relationship IDs

Generate a unique GUID (UUID v4) for the following TMDL objects as a `lineageTag` property:

- Each table (`lineageTag` under the `table` declaration)
- Each measure (`lineageTag` under the `measure` declaration)
- Each column (`lineageTag` under the `column` declaration)

Generate a unique GUID as the **name** for each relationship:

- Each relationship uses the GUID as its identifier on the declaration line: `relationship <guid>`
- Relationships do **NOT** have a `lineageTag` property — do NOT add `lineageTag` inside a relationship block

Format: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`

## Data Type and Source Provider Type Mapping

Every column MUST include both `dataType` and `sourceProviderType`. Some types also require a `formatString`.

| Databricks SQL Type | TMDL `dataType` | `sourceProviderType` | `formatString` |
|---|---|---|---|
| `STRING`, `VARCHAR` | `string` | `nvarchar(65535)` | (none) |
| `INT` | `int64` | `int` | `0` |
| `BIGINT` | `int64` | `bigint` | `0` |
| `DOUBLE`, `FLOAT` | `double` | `double` | (none, add `annotation PBI_FormatHint = {"isGeneralNumber":true}`) |
| `DECIMAL` | `double` | `double` | (none, add `annotation PBI_FormatHint = {"isGeneralNumber":true}`) |
| `DATE` | `dateTime` | `date` | `Long Date` |
| `TIMESTAMP` | `dateTime` | `datetime2` | `General Date` |
| `BOOLEAN` | `boolean` | `bit` | `"""TRUE""";"""TRUE""";"""FALSE"""` |

**Column examples from reference:**

```tmdl
 column customer_key
  dataType: int64
  formatString: 0
  sourceProviderType: bigint
  lineageTag: <guid>
  summarizeBy: none
  sourceColumn: customer_key

  annotation SummarizationSetBy = Automatic

 column state
  dataType: string
  sourceProviderType: nvarchar(65535)
  lineageTag: <guid>
  summarizeBy: none
  sourceColumn: state

  annotation SummarizationSetBy = Automatic

 column price
  dataType: double
  sourceProviderType: double
  lineageTag: <guid>
  summarizeBy: sum
  sourceColumn: price

  annotation SummarizationSetBy = Automatic

  annotation PBI_FormatHint = {"isGeneralNumber":true}

 column date
  dataType: dateTime
  formatString: Long Date
  sourceProviderType: date
  lineageTag: <guid>
  summarizeBy: none
  sourceColumn: date

  annotation SummarizationSetBy = Automatic

  annotation UnderlyingDateTimeDataType = Date
```

## Validation Checklist

1. All tables from source and joins have corresponding TMDL files
2. All relationships match the YAML joins (correct from/to columns)
3. All measures are converted with proper DAX syntax and table qualifiers
4. All format strings are correctly mapped
5. All lineage tags are unique GUIDs
6. M-Code partitions reference correct catalog/schema/table
7. Role-playing dimensions use the correct strategy: inactive relationship for optional alternate roles, or separate active role-playing tables when both roles must filter simultaneously
8. **ALL columns** from each selected table are included (not just query-referenced columns)
9. `database.tmdl` uses `compatibilityLevel: 1600` (not `1567`)
10. Every derived SQL alias used by visuals is materialized in TMDL as either a calculated column or a measure
11. **Every derived field with `semanticKind: dimension` has `materializationType: calculatedColumn`.** A derived field routed to `Series`/Legend that resolves to a `measure` is a **blocking error** — do not proceed to Stage 2 until it is re-materialized as a calculated column.
12. Data-anchored last-N-month requests produce a helper flag or measure bound to the correct date role before visual generation

## Error Handling

| Error | Resolution |
|---|---|
| Unknown SQL function in measure expr | Add inline comment `/* TODO: convert <function> */` |
| Missing join for a dimension's table prefix | Skip the dimension, log a warning |
| Ambiguous column reference (no table prefix) | Default to fact table |
| Unsupported window function syntax | Convert to basic CALCULATE with TODO comment |

## Resources

- `references/sql-to-dax-reference.md` — Comprehensive SQL to DAX conversion patterns and examples
