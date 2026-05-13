# Clarification Questions

Standard question bank emitted into `data-model.json.openQuestions[]` when the connector cannot auto-resolve a piece of the data model. Each entry has an `id`, `scope`, and the literal `question` text the orchestrator should surface to the user.

## Connection-Level Questions

| Scope | Trigger | Question |
|---|---|---|
| connection | Missing source path/URL | "Where is the data located? Please provide a file path, connection string, or URL." |
| connection | Missing Databricks warehouse | "What is your Databricks SQL warehouse ID?" |
| connection | Missing Databricks hostname | "What is the Databricks workspace hostname (without https://)?" |
| connection | Missing Snowflake account | "What is your Snowflake account identifier?" |
| connection | Missing BigQuery project | "What is the GCP project ID for your BigQuery dataset?" |
| connection | Auth method unclear | "Should I use a service account, OAuth, or username/password to authenticate?" |
| connection | Excel file not found | "I can't find `<path>`. Could you double-check the file path?" |

## Scope Questions

| Scope | Trigger | Question |
|---|---|---|
| scope | Too many tables discovered (>20) | "I found N tables. Which ones are relevant to this dashboard?" |
| scope | Multiple Excel sheets, some look like metadata | "Sheets `<list>` look like metadata or instructions — should I exclude them?" |
| scope | REST API with many endpoints | "Which endpoints should I include?" |

## Table-Classification Questions

| Scope | Trigger | Question |
|---|---|---|
| classification | No clear fact table | "I don't see an obvious fact table. Which table holds the numeric measures you care about?" |
| classification | Multiple fact-shaped tables | "Tables `<list>` all look like fact tables. Are they separate facts, or should I treat one as primary?" |
| classification | Table has no recognizable role | "What is `<table>` — a fact (measures), a dimension (descriptive attributes), or something else?" |
| classification | Ambiguous grain | "What is the grain of `<fact_table>` — one row per order, per order line, per transaction?" |

## Relationship Questions

| Scope | Trigger | Question |
|---|---|---|
| relationship | FK inferred from naming | "I'm inferring that `<fact>.<col>` joins to `<dim>.<col>` based on column names. Is that correct?" |
| relationship | Multiple plausible joins | "`<fact>.<col>` could join to either `<dim_a>.<col>` or `<dim_b>.<col>`. Which one is correct?" |
| relationship | No FK candidates | "I don't see how `<table>` joins to the rest of the model. Should I leave it standalone or do you know the join key?" |

## Date-Dimension Questions

| Scope | Trigger | Question |
|---|---|---|
| date | No date dimension found | "I don't see a dedicated date dimension. Should I generate one, or use the date column on `<fact>` directly?" |
| date | Multiple date columns on fact | "The fact table has multiple date columns (`<list>`). Which is the primary date for analysis? Are any role-playing (purchase vs. delivery)?" |
| date | Date column has gaps | "The date column has gaps. Should I generate a continuous date dimension covering the full range?" |

## Measure Questions

| Scope | Trigger | Question |
|---|---|---|
| measure | No obvious measure columns | "Which columns on `<fact>` should I treat as measures (numeric values to aggregate)?" |
| measure | Multiple currency columns | "I see several currency columns. Which currency are they in, and should they all be aggregated as SUM?" |
| measure | Boolean-looking column | "`<col>` is a 0/1 flag. Should I count rows where it's 1, or sum it directly?" |

## Output Mode Questions

| Scope | Trigger | Question |
|---|---|---|
| mode | Source supports both | "Should I use DirectQuery (live connection, larger model) or Import (snapshot, faster but stale)?" |

## How the Orchestrator Should Surface These

The orchestrator should batch related questions (e.g., all `relationship` questions in one prompt) rather than firing them serially. Always include enough context so the user can answer in one round-trip.
