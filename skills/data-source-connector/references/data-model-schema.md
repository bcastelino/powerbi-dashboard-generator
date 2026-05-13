# data-model.json Schema

The normalized, source-agnostic representation of a data model. Produced by `data-source-connector` and consumed by `semantic-mapper`, `visual-selector`, and `nlq-dashboard-orchestrator`.

## Top-Level Shape

```json
{
  "source": { ... },
  "tables": [ ... ],
  "relationships": [ ... ],
  "mCodeAdapter": { ... },
  "openQuestions": [ ... ]
}
```

## `source`

```json
{
  "type": "databricks | snowflake | bigquery | synapse | sqlserver | postgres | mysql | oracle | excel | csv | parquet | odata | rest | sharepoint",
  "connection": { /* source-specific fields; never includes secrets */ },
  "discoveredAt": "ISO-8601 timestamp"
}
```

## `tables[]`

```json
{
  "name": "string (TMDL-safe, snake_case)",
  "physicalName": "string (as it exists in the source)",
  "role": "fact | dimension | date dimension | bridge | unknown",
  "grain": "string (one-line description, optional)",
  "rowCountEstimate": "integer (optional)",
  "columns": [
    {
      "name": "string (TMDL-safe)",
      "physicalName": "string",
      "dataType": "string | int64 | double | dateTime | boolean",
      "sourceProviderType": "string (e.g. nvarchar(65535), bigint, double)",
      "isPrimaryKey": "boolean (optional)",
      "isForeignKey": "boolean (optional)",
      "foreignKey": { "table": "string", "column": "string" },
      "nullable": "boolean (optional)",
      "formatHint": "currency | percentage | number | date | datetime (optional)"
    }
  ],
  "sampleRows": [
    { "<column_name>": "<value>", ... }
  ]
}
```

## `relationships[]`

```json
{
  "from": { "table": "string", "column": "string" },
  "to":   { "table": "string", "column": "string" },
  "cardinality": "many-to-one | one-to-many | one-to-one | many-to-many",
  "isActive": "boolean",
  "inferredFrom": "fk constraint | naming convention | user input"
}
```

## `mCodeAdapter`

```json
{
  "mode": "directQuery | import",
  "templates": {
    "<table_name>": "let ... in ... (M-Code string, no placeholder markers)"
  }
}
```

Each entry is a fully resolved M-Code block — no `<placeholder>` markers remain. `semantic-mapper` copies the relevant template directly into the TMDL `partition <table> = m / source = ...` block.

## `openQuestions[]`

```json
{
  "id": "string (unique within this file)",
  "scope": "connection | scope | classification | relationship | date | measure | mode",
  "question": "string (literal text to show the user)",
  "context": "object (optional, machine-readable hints to help the user respond)"
}
```

The orchestrator must resolve all `openQuestions` before passing Gate A.

## Validation

When `semantic-mapper` ingests `data-model.json`, it expects:

1. `tables[].name` matches TMDL naming rules (alphanumeric + underscore, doesn't start with digit)
2. Every relationship references existing tables and columns
3. `mCodeAdapter.templates` covers every table in `tables[]`
4. At least one table has `role: "fact"`
5. `openQuestions` is empty
