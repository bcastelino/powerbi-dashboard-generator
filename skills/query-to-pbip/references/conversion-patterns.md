# Conversion Patterns Reference

Complete reference for converting Databricks Genie YAML metric views to Power BI TMDL format. Use this document when executing the semantic-mapper sub-skill (Stage 1).

## SQL-to-DAX Function Mapping

## Derived SQL Alias Materialization

When the query includes `SELECT ... AS <alias>` outputs that are not already in the semantic model, materialize them in Stage 1 before visual generation.

### Artifact Selection Rules

| SQL Alias Pattern | Semantic Artifact | Default Target |
|---|---|---|
| Row-level `CASE`, `COALESCE`, `CAST`, string/date transform | Calculated column | Owning dimension/fact table |
| Aggregate or ratio of aggregates (`SUM`, `AVG`, `COUNT`, `DIVIDE`) | Measure | Fact table |
| Window/rank expression (`ROW_NUMBER`, `RANK`) | Calculated column (if deterministic at row grain **and** only references existing source columns), otherwise measure + fallback note | Table at expression grain |

### Generic Examples

**SQL alias (categorical flag):**

```sql
CASE WHEN volume_rank <= 5 THEN 'Top 5' ELSE 'Non Top 5' END AS Top Flag
```

**TMDL artifact (calculated column):**

Calculated columns use the inline DAX expression syntax: `column 'Name' = <DAX expression>`. The SQL `CASE` expression must be translated to equivalent DAX (e.g., `IF`). Calculated columns must **NOT** include `sourceColumn:` or `sourceProviderType:` — these are source column properties only.

**DirectQuery restriction:** Calculated columns on DirectQuery tables cannot use iterator functions (`RANKX`, `SUMX`, `AVERAGEX`, `COUNTX`, `MAXX`, `MINX`, `FILTER`, `ADDCOLUMNS`, `SELECTCOLUMNS`, etc.). The DAX expression must only use simple scalar functions and direct column references. If a rank or window computation is needed, reference the **pre-existing source column** (e.g., `dim_product[volume_rank]`) rather than recomputing it with `RANKX`. If no suitable source column exists, convert to a **measure** instead of a calculated column.

```tmdl
column 'Top Flag' = IF(dim_product[volume_rank] <= 5, "Top 5", "Non Top 5")
    dataType: string
    lineageTag: <guid>
    summarizeBy: none

    annotation SummarizationSetBy = Automatic
```

> **Correct:** `IF(dim_product[volume_rank] <= 5, ...)` — references existing source column `volume_rank`.
> **Wrong:** `IF(RANKX(ALL(dim_product), dim_product[volume]) <= 5, ...)` — uses `RANKX` iterator, which is forbidden in DirectQuery calculated columns.

**SQL alias (aggregate ratio):**

```sql
SUM(total_value) / NULLIF(COUNT(DISTINCT order_id), 0) AS AOV
```

**TMDL artifact (measure):**

```tmdl
measure 'AOV' = DIVIDE(SUM(fact_sales[total_value]), DISTINCTCOUNT(fact_sales[order_id]))
    formatString: #,0.00
    lineageTag: <guid>
```

Visual binding must reference these materialized artifacts only; do not bind visuals directly to transient SQL aliases.

> **Power BI Series/Legend column-only constraint:** Power BI does not allow measure fields in Legend or Series buckets. Any derived alias classified as `Nominal`/categorical — including `CASE` expressions that reference window function results (e.g. `CASE WHEN rank <= 5 THEN ... END`) — **must always produce a calculated column**, never a measure. The window/rank fallback to `measure` applies only when the result is a numeric aggregate with `semanticKind: measure`. If in doubt, default to `calculatedColumn` for any string-typed or binary-flag derived alias.

### Aggregation Functions

| SQL Expression (Genie YAML `expr`) | DAX Equivalent | Notes |
|---|---|---|
| `SUM(column)` | `SUM(table[column])` | Direct mapping; qualify column with table name |
| `COUNT(column)` | `COUNT(table[column])` | Counts non-blank values |
| `COUNT(*)` | `COUNTROWS(table)` | Count all rows including blanks |
| `COUNT(DISTINCT column)` | `DISTINCTCOUNT(table[column])` | Distinct count |
| `AVG(column)` | `AVERAGE(table[column])` | Average value |
| `MIN(column)` | `MIN(table[column])` | Minimum value |
| `MAX(column)` | `MAX(table[column])` | Maximum value |

### Division and Null Handling

| SQL Expression | DAX Equivalent | Notes |
|---|---|---|
| `a / NULLIF(b, 0)` | `DIVIDE(a, b)` | DIVIDE returns BLANK for division by zero |
| `a / b` | `DIVIDE(a, b)` | Always use DIVIDE for safe division |
| `COALESCE(a, b)` | `IF(ISBLANK(a), b, a)` | Or use `COALESCE(a, b)` in newer DAX |
| `CASE WHEN x THEN a ELSE b END` | `IF(x, a, b)` | Simple conditional |
| `NULLIF(a, b)` | `IF(a = b, BLANK(), a)` | Return BLANK if equal |

### Window Functions (Rolling Calculations)

YAML window definitions translate to DAX time intelligence:

**YAML Pattern:**

```yaml
window:
  order: order_date
  range:
    trailing: 7
    frame: day
```

**DAX Translation:**

```dax
CALCULATE(
    [Base Measure],
    DATESINPERIOD(
        dim_date[date],
        MAX(dim_date[date]),
        -7,
        DAY
    )
)
```

**With active role-playing date table (delivery timeline):**

```dax
CALCULATE(
    [Base Measure],
    DATESINPERIOD(
        dim_date_delivery[date],
        MAX(dim_date_delivery[date]),
        -30,
        DAY
    )
)
```

**Data-anchored last-N-month flag:**

```dax
measure 'Show Last 12 Purchase Months' =
VAR MaxAvailableDate = MAXX(ALL(fact_sales), RELATED('dim_date'[date]))
VAR WindowStart = EOMONTH(MaxAvailableDate, -12) + 1
VAR WindowEnd = EOMONTH(MaxAvailableDate, 0)
VAR AxisDate = MAX('dim_date'[date])
RETURN IF(NOT ISBLANK(MaxAvailableDate) && AxisDate >= WindowStart && AxisDate <= WindowEnd, 1, 0)
```

### Subquery Patterns

**SQL with subquery (e.g., Active Customers):**

```sql
COUNT(DISTINCT customer_unique_id) WHERE customer_key IN (SELECT customer_key FROM fact_sales)
```

**DAX equivalent:**

```dax
CALCULATE(
    DISTINCTCOUNT(dim_customer[customer_unique_id]),
    RELATEDTABLE(fact_sales)
)
```

## Format String Mapping

| YAML Format | TMDL `formatString` | Annotation |
|---|---|---|
| `type: currency, currency_code: USD` | `$#,0.00` | `Format = <Format Currency=\"USD\" />` |
| `type: currency, currency_code: USD, decimal_places: 0` | `$#,0` | `Format = <Format Currency=\"USD\" />` |
| `type: percentage` | `0.0%` | None |
| `type: percentage, decimal_places: 2` | `0.00%` | None |
| `type: number` | `#,0` | None |
| `type: number, decimal_places: 2` | `#,0.00` | None |
| `type: decimal, decimal_places: 1` | `0.0` | None |

### Format Annotation Example

```tmdl
measure 'Total Revenue (GMV)' = SUM(fact_sales[total_value])
    formatString: $#,0.00
    lineageTag: <guid>

    annotation Format = <Format Currency="USD" />
```

## TMDL File Templates

### database.tmdl

The `database` declaration has no name argument. Use `compatibilityLevel: 1600` (not `1567` — downgrading causes a Power BI error).

```tmdl
database
 compatibilityLevel: 1600
```

### model.tmdl

The `model.tmdl` file must include model properties, annotations, `ref table` declarations for every table, and a `ref cultureInfo` declaration. **Each `ref` statement must be on its own separate line** — concatenating them causes Power BI Desktop parsing errors (`InvalidObjectHeader`).

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

**Formatting rules:**

- Must include `dataAccessOptions` block with `legacyRedirects` and `returnErrorValuesAsNull`
- Must include `annotation __PBI_TimeIntelligenceEnabled = 1`
- Do NOT include `discourageImplicitMeasures` — it is not in the reference model
- Each `ref table <tablename>` on its own line (one per line, never concatenated)
- `ref cultureInfo en-US` on its own line (no quotes around `en-US`)
- Blank lines between the model properties block, annotations, ref table block, and ref cultureInfo
- Tab indentation under `model Model`
- Table names unquoted unless they contain spaces or special characters

### relationships.tmdl

The `<guid>` is the relationship **name/identifier** on the declaration line. Relationships do **NOT** support a `lineageTag` property — adding one causes `TMDL Format Error: UnknownKeyword`. Each relationship must include `annotation PBI_IsFromSource = FS`.

```tmdl
relationship <guid>
 fromColumn: fact_sales.customer_key
 toColumn: dim_customer.customer_key

 annotation PBI_IsFromSource = FS

relationship <guid>
 fromColumn: fact_sales.seller_key
 toColumn: dim_seller.seller_key

 annotation PBI_IsFromSource = FS
```

**Active role-playing relationship (simultaneous date roles):**

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

**Inactive relationship fallback (measure-only alternate date role):**

```tmdl
relationship <guid>
 isActive: false
 fromColumn: fact_sales.delivered_date_key
 toColumn: dim_date.date_key

 annotation PBI_IsFromSource = FS
```

### Table TMDL Structure

**Important: Include ALL columns from each table.** When a table is selected for the model, every column in that source table must be defined in the TMDL file — not just the columns referenced in the query. Omitting columns causes data incompleteness and can break relationships and measures.

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

**Column property requirements (from reference):**

- Every column MUST include `sourceProviderType` (e.g., `bigint`, `nvarchar(65535)`, `double`, `date`, `datetime2`)
- Every column MUST include `annotation SummarizationSetBy = Automatic`
- `int64` columns MUST include `formatString: 0`
- `dateTime` columns MUST include `formatString: Long Date` (for date) or `General Date` (for timestamp)
- `double` columns MUST include `annotation PBI_FormatHint = {"isGeneralNumber":true}`
- `string` columns do NOT need a `formatString`

## Join-to-Relationship Mapping

### `using:` (Same Column Name)

**YAML:**

```yaml
joins:
  - name: dim_customer
    source: wl_internal.olist_ecommerce.dim_customer
    using:
      - customer_key
```

**TMDL (relationships.tmdl):**

```tmdl
relationship <guid>
    fromColumn: fact_sales.customer_key
    toColumn: dim_customer.customer_key
```

### `on:` (Different Column Names)

**YAML:**

```yaml
joins:
  - name: dim_date
    source: wl_internal.olist_ecommerce.dim_date
    on:
      purchase_date_key: date_key
```

**TMDL (relationships.tmdl):**

```tmdl
relationship <guid>
    fromColumn: fact_sales.purchase_date_key
    toColumn: dim_date.date_key
```

## M-Code Partition Pattern

Extract the three-part table identifier from the YAML `source` field:

**YAML source:** `wl_internal.olist_ecommerce.fact_sales`

- Catalog: `wl_internal`
- Schema: `olist_ecommerce`
- Table: `fact_sales`

**Important:** Always use the Databricks connection parameters (workspace hostname and SQL warehouse ID) provided as inputs to the semantic-mapper skill. Never hardcode these values.

**Critical M-Code formatting rules:**

- **Hostname**: Use the bare hostname WITHOUT `https://` prefix (e.g., `"wl-dbr-dbr-dev-ws-wl.cloud.databricks.com"`, NOT `"https://wl-dbr-dbr-dev-ws-wl.cloud.databricks.com"`)
- **Warehouse ID**: Use the `/sql/1.0/warehouses/<id>` path format (e.g., `"/sql/1.0/warehouses/9d2b45a6a9dda4aa"`)
- **Catalog/Database**: Use empty strings `[Catalog = "", Database = ""]`, NOT `null` values

**M-Code template:**

```m
let
    Source = DatabricksMultiCloud.Catalogs("<hostname>", "/sql/1.0/warehouses/<warehouse_id>", [Catalog = "", Database = ""]),
    <catalog>_Database = Source{[Name="<catalog>",Kind="Database"]}[Data],
    <schema>_Schema = <catalog>_Database{[Name="<schema>",Kind="Schema"]}[Data],
    <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
in
    <table>_Table
```

**Example with actual values (for illustration only — always use provided connection params):**

```m
let
    Source = DatabricksMultiCloud.Catalogs("wl-dbr-dbr-dev-ws-wl.cloud.databricks.com", "/sql/1.0/warehouses/9d2b45a6a9dda4aa", [Catalog = "", Database = ""]),
    wl_internal_Database = Source{[Name="wl_internal",Kind="Database"]}[Data],
    olist_ecommerce_Schema = wl_internal_Database{[Name="olist_ecommerce",Kind="Schema"]}[Data],
    fact_sales_Table = olist_ecommerce_Schema{[Name="fact_sales",Kind="Table"]}[Data]
in
    fact_sales_Table
```

## GUID Generation

Every TMDL object requires a unique `lineageTag` in standard GUID format:

```
xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx
```

Where:

- `x` = random hexadecimal digit (0-9, a-f)
- `4` = version indicator (always 4)
- `y` = variant indicator (8, 9, a, or b)

Generate using Python:

```python
import uuid
lineage_tag = str(uuid.uuid4())
```

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
