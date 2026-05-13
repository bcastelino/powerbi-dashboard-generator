# Connection Patterns

Per-source connection recipes and M-Code templates emitted into `data-model.json.mCodeAdapter.templates`. Each block is keyed by `<placeholder>` markers that `data-source-connector` substitutes at runtime.

## Databricks (DirectQuery)

Required inputs: `hostname` (bare domain, no `https://`), `warehouse_id`, `catalog`, `schema`.

```text
let
    Source = DatabricksMultiCloud.Catalogs("<hostname>", "/sql/1.0/warehouses/<warehouse_id>", [Catalog = "", Database = ""]),
    <catalog>_Database = Source{[Name="<catalog>",Kind="Database"]}[Data],
    <schema>_Schema = <catalog>_Database{[Name="<schema>",Kind="Schema"]}[Data],
    <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
in
    <table>_Table
```

## Snowflake (DirectQuery)

Required: `server`, `warehouse`, `database`, `schema`.

```text
let
    Source = Snowflake.Databases("<server>", "<warehouse>"),
    <database>_Database = Source{[Name="<database>",Kind="Database"]}[Data],
    <schema>_Schema = <database>_Database{[Name="<schema>",Kind="Schema"]}[Data],
    <table>_Table = <schema>_Schema{[Name="<table>",Kind="Table"]}[Data]
in
    <table>_Table
```

## BigQuery (DirectQuery)

Required: `project`, `dataset`.

```text
let
    Source = GoogleBigQuery.Database(),
    <project>_Project = Source{[Name="<project>"]}[Data],
    <dataset>_Schema = <project>_Project{[Name="<dataset>",Kind="Schema"]}[Data],
    <table>_Table = <dataset>_Schema{[Name="<table>",Kind="Table"]}[Data]
in
    <table>_Table
```

## SQL Server / Azure Synapse (DirectQuery)

Required: `server`, `database`.

```text
let
    Source = Sql.Database("<server>", "<database>"),
    <schema>_<table> = Source{[Schema="<schema>",Item="<table>"]}[Data]
in
    <schema>_<table>
```

## PostgreSQL (DirectQuery or Import)

Required: `host`, `port`, `database`, `schema`.

```text
let
    Source = PostgreSQL.Database("<host>:<port>", "<database>"),
    <schema>_<table> = Source{[Schema="<schema>",Item="<table>"]}[Data]
in
    <schema>_<table>
```

## MySQL (DirectQuery or Import)

```text
let
    Source = MySQL.Database("<host>:<port>", "<database>"),
    <table>_Table = Source{[Schema="<database>",Item="<table>"]}[Data]
in
    <table>_Table
```

## Oracle (DirectQuery)

```text
let
    Source = Oracle.Database("<host>:<port>/<service_name>"),
    <schema>_<table> = Source{[Schema="<schema>",Item="<table>"]}[Data]
in
    <schema>_<table>
```

## Excel (Import)

Required: `path`, `sheet`.

```text
let
    Source = Excel.Workbook(File.Contents("<path>"), null, true),
    <sheet>_Sheet = Source{[Item="<sheet>",Kind="Sheet"]}[Data],
    #"Promoted Headers" = Table.PromoteHeaders(<sheet>_Sheet, [PromoteAllScalars=true])
in
    #"Promoted Headers"
```

## CSV (Import)

Required: `path`, `columnCount`.

```text
let
    Source = Csv.Document(File.Contents("<path>"), [Delimiter=",", Columns=<columnCount>, Encoding=65001, QuoteStyle=QuoteStyle.Csv]),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true])
in
    #"Promoted Headers"
```

## Parquet (Import)

```text
let
    Source = Parquet.Document(File.Contents("<path>"))
in
    Source
```

## OData (Import)

Required: `service_url`, `entity_set`.

```text
let
    Source = OData.Feed("<service_url>", null, [Implementation="2.0"]),
    <entity_set>_Table = Source{[Name="<entity_set>",Signature="table"]}[Data]
in
    <entity_set>_Table
```

## REST API (Import)

Required: `base_url`, `endpoint`. Returns vary; standardize on JSON array of objects.

```text
let
    Source = Json.Document(Web.Contents("<base_url>", [RelativePath="<endpoint>"])),
    AsTable = Table.FromList(Source, Splitter.SplitByNothing(), null, null, ExtraValues.Error),
    Expanded = Table.ExpandRecordColumn(AsTable, "Column1", Record.FieldNames(Source{0}))
in
    Expanded
```

## SharePoint Lists (Import)

Required: `site_url`, `list_name`.

```text
let
    Source = SharePoint.Tables("<site_url>", [ApiVersion = 15]),
    <list_name>_List = Source{[Title="<list_name>"]}[Items]
in
    <list_name>_List
```

## Placeholder Substitution Rules

When emitting M-Code into `data-model.json.mCodeAdapter.templates[<table>]`, replace placeholders with the corresponding values from the source descriptor and discovered table metadata. Do NOT leave any `<placeholder>` markers in the final output — `semantic-mapper` will copy these verbatim into TMDL partitions.
