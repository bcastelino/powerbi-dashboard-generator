---
name: data-source-connector
description: Source-agnostic adapter that introspects any data storage (SQL databases, cloud warehouses, Excel/CSV files, OData/REST APIs, SharePoint lists) and emits a normalized data-model.json describing tables, columns, types, and relationships. Use this skill at the start of the dashboard pipeline whenever the user has not provided a structured data model. It also emits a clarification question list when schema cannot be auto-discovered, and produces the source-specific M-Code / import block consumed by semantic-mapper.
---

# Data Source Connector

Universal data-source adapter for the Power BI dashboard pipeline. This skill abstracts away the specifics of every supported source and produces a single, normalized artifact — `data-model.json` — that downstream skills (`semantic-mapper`, `visual-selector`, `visual-generator`) can consume without knowing where the data actually came from.

## When to Use This Skill

- The orchestrator (or the user) has identified a source but no structured data model exists
- The agent needs to enumerate tables, columns, types, and relationships from any backend
- A Genie YAML metric view is **not** available (use this skill instead of `semantic-mapper`'s YAML path)
- The agent needs the source-specific M-Code / connection block to embed in TMDL partitions

## Supported Sources

| Source Type | `type` value | Required Inputs |
|---|---|---|
| Databricks | `databricks` | `hostname`, `warehouse_id`, `catalog`, `schema` |
| Snowflake | `snowflake` | `account`, `warehouse`, `database`, `schema`, `role` |
| BigQuery | `bigquery` | `project`, `dataset` |
| Azure Synapse | `synapse` | `server`, `database` |
| SQL Server | `sqlserver` | `server`, `database` |
| PostgreSQL | `postgres` | `host`, `port`, `database`, `schema` |
| MySQL | `mysql` | `host`, `port`, `database` |
| Oracle | `oracle` | `host`, `port`, `service_name` |
| Excel | `excel` | `path` (`.xlsx` file); each sheet becomes a table |
| CSV | `csv` | `path` or directory of CSVs; each file becomes a table |
| Parquet | `parquet` | `path` or directory |
| OData | `odata` | `service_url` |
| REST API | `rest` | `base_url`, `endpoints[]`, `auth` |
| SharePoint Lists | `sharepoint` | `site_url`, `list_names[]` |

## Inputs

- **Source descriptor** — `{ type, ...connection params }` from the orchestrator or the user
- **Scope hint** (optional) — which tables / sheets / endpoints to include (defaults to all)
- **Sampling preference** (optional) — number of sample rows to capture per table (default 5)

## Outputs

### Primary: `data-model.json`

Source-agnostic, normalized representation. Schema:

```json
{
  "source": {
    "type": "excel",
    "connection": { "path": "C:/data/sales.xlsx" },
    "discoveredAt": "2026-05-13T11:00:00Z"
  },
  "tables": [
    {
      "name": "fact_sales",
      "physicalName": "Orders",
      "role": "fact",
      "grain": "one row per order line",
      "rowCountEstimate": 50000,
      "columns": [
        {
          "name": "order_id",
          "physicalName": "OrderID",
          "dataType": "int64",
          "sourceProviderType": "bigint",
          "isPrimaryKey": true,
          "nullable": false
        },
        {
          "name": "customer_key",
          "physicalName": "CustomerID",
          "dataType": "int64",
          "sourceProviderType": "bigint",
          "isForeignKey": true,
          "foreignKey": { "table": "dim_customer", "column": "customer_key" }
        },
        {
          "name": "total_value",
          "physicalName": "TotalValue",
          "dataType": "double",
          "sourceProviderType": "double",
          "formatHint": "currency"
        }
      ],
      "sampleRows": [
        { "order_id": 1, "customer_key": 42, "total_value": 199.99 }
      ]
    }
  ],
  "relationships": [
    {
      "from": { "table": "fact_sales", "column": "customer_key" },
      "to":   { "table": "dim_customer", "column": "customer_key" },
      "cardinality": "many-to-one",
      "isActive": true,
      "inferredFrom": "naming convention"
    }
  ],
  "mCodeAdapter": {
    "mode": "import",
    "templates": {
      "fact_sales": "let Source = Excel.Workbook(File.Contents(\"C:/data/sales.xlsx\"), null, true), Orders_Sheet = Source{[Item=\"Orders\",Kind=\"Sheet\"]}[Data], #\"Promoted Headers\" = Table.PromoteHeaders(Orders_Sheet, [PromoteAllScalars=true]) in #\"Promoted Headers\""
    }
  },
  "openQuestions": [
    {
      "id": "q1",
      "scope": "relationship",
      "question": "Is the relationship between fact_sales.customer_key and dim_customer.customer_key correct? It was inferred from column-name similarity, not from a foreign key constraint."
    }
  ]
}
```

### Secondary: Clarification report

If schema cannot be fully discovered (missing credentials, ambiguous grain, no FK constraints), emit `openQuestions[]` for the orchestrator to surface to the user.

## Workflow

### Step 1: Validate Connection Inputs

For each source type, check that required inputs are present. If any are missing, emit a clarification question and stop.

Examples:

- `databricks` missing `warehouse_id` → ask: *"What is the Databricks SQL warehouse ID?"*
- `excel` missing `path` → ask: *"What is the full path to the Excel file?"*
- `sqlserver` missing credentials → ask: *"Is this a trusted-connection database, or do I need a username and password?"*

See `references/clarification-questions.md` for the full question bank.

### Step 2: Probe the Source

Run `scripts/introspect_source.py` (or the source-specific adapter) to:

1. **List tables / sheets / endpoints**
2. **For each table**: list columns with native types, nullability, primary key flags
3. **Sample rows**: pull 5 sample rows per table (configurable)
4. **Foreign key discovery**:
   - If the source supports FK constraints (SQL databases) → use them directly
   - Otherwise → infer from column-name patterns (`<table>_key`, `<table>_id`, identical names across tables) and flag as `inferredFrom: naming convention` for user confirmation at Gate A

### Step 3: Classify Tables (Fact vs. Dimension)

Heuristics:

| Signal | Likely Role |
|---|---|
| Has multiple FK columns + a numeric measure column | `fact` |
| Name contains `fact_`, `sales`, `orders`, `transactions`, `events` | `fact` |
| Name contains `dim_`, `customers`, `products`, `dates`, `geography` | `dimension` |
| Only one PK column + descriptive columns | `dimension` |
| Has a date column with daily continuity | `date dimension` |

If unsure, add to `openQuestions[]` and ask the user at Gate A.

### Step 4: Normalize Types

Map source-native types to TMDL types (consumed by `semantic-mapper`):

| Source Type | `dataType` | `sourceProviderType` |
|---|---|---|
| `STRING`, `VARCHAR`, `NVARCHAR`, `TEXT` | `string` | `nvarchar(65535)` |
| `INT`, `INTEGER`, `INT32` | `int64` | `int` |
| `BIGINT`, `LONG` | `int64` | `bigint` |
| `DOUBLE`, `FLOAT`, `REAL`, `DECIMAL`, `NUMERIC` | `double` | `double` |
| `DATE` | `dateTime` | `date` |
| `DATETIME`, `TIMESTAMP`, `DATETIME2` | `dateTime` | `datetime2` |
| `BOOLEAN`, `BIT` | `boolean` | `bit` |

For Excel/CSV with no declared types, sniff from sample rows.

### Step 5: Generate the M-Code Adapter Block

Each source has a different M-Code template. Per-source templates live in `references/connection-patterns.md`. Examples:

**Databricks (DirectQuery):**

```text
let
    Source = DatabricksMultiCloud.Catalogs("<hostname>", "/sql/1.0/warehouses/<warehouse_id>", [Catalog = "", Database = ""]),
    <catalog>_Database = Source{[Name="<catalog>",Kind="Database"]}[Data],
    <schema>_Schema = <catalog>_Database{[Name="<schema>",Kind="Schema"]}[Data],
    <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
in
    <table>_Table
```

**Excel (Import):**

```text
let
    Source = Excel.Workbook(File.Contents("<path>"), null, true),
    <sheet>_Sheet = Source{[Item="<sheet>",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(<sheet>_Sheet, [PromoteAllScalars=true])
in
    #"Promoted Headers"
```

**CSV (Import):**

```text
let
    Source = Csv.Document(File.Contents("<path>"), [Delimiter=",", Columns=<n>, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    #"Promoted Headers"
```

**SQL Server (DirectQuery):**

```text
let
    Source = Sql.Database("<server>", "<database>"),
    <schema>_<table> = Source{[Schema="<schema>",Item="<table>"]}[Data]
in
    <schema>_<table>
```

The connector emits one M-Code block per table into `data-model.json` → `mCodeAdapter.templates`.

### Step 6: Mode Selection

Set `mCodeAdapter.mode` based on source:

| Source | Mode |
|---|---|
| Databricks, Snowflake, BigQuery, Synapse, SQL Server (large), Oracle | `directQuery` |
| Excel, CSV, Parquet, SharePoint List, REST API | `import` |
| Postgres, MySQL | `directQuery` if user opts in, otherwise `import` |

### Step 7: Emit `openQuestions`

Append a question for every uncertainty:

- Ambiguous fact/dimension classification
- Inferred (not declared) foreign keys
- Multiple date columns (which is the primary date?)
- Tables with no measurable columns (skip or include?)
- Files with multiple sheets where some look like junk (e.g., metadata, instructions)

## Outputs Handed to Downstream

| File | Consumer | Purpose |
|---|---|---|
| `data-model.json` | `semantic-mapper`, `visual-selector`, `nlq-dashboard-orchestrator` | Normalized model |
| `data-model.json.openQuestions[]` | `nlq-dashboard-orchestrator` (Gate A) | Drive clarification dialog |
| `data-model.json.mCodeAdapter` | `semantic-mapper` | TMDL partition source blocks |

## Validation Checklist

1. Every table has at least one column
2. Every relationship references existing `{table, column}` on both sides
3. Every column has both `dataType` and `sourceProviderType`
4. Exactly zero or one date-dimension table is flagged as `role: "date dimension"` per date role
5. At least one table is classified as `fact`
6. `mCodeAdapter.templates` has one entry per table in `tables[]`
7. `openQuestions` is empty OR every entry has a unique `id` and a non-empty `question`

## Error Handling

| Error | Resolution |
|---|---|
| Cannot reach source | Surface error verbatim; ask user for corrected connection params |
| Authentication failed | Ask user for credentials; never store them in `data-model.json` |
| Empty schema (no tables found) | Stop and ask the user to verify scope |
| Table with zero columns | Skip and log a warning |
| Source type unsupported | Ask user to convert to a supported source (e.g., export DB query to CSV) |

## Resources

- **`scripts/introspect_source.py`** — Main connector entry point; routes to source-specific adapters
- **`references/connection-patterns.md`** — Per-source connection recipes and M-Code templates
- **`references/clarification-questions.md`** — Standard question bank for missing/ambiguous inputs
- **`references/data-model-schema.md`** — Full JSON schema for `data-model.json`
