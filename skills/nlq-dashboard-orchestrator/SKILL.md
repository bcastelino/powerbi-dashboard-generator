---
name: nlq-dashboard-orchestrator
description: Top-level entry point that turns a natural-language dashboard request into a complete Power BI Desktop Project (PBIP). This skill should be used whenever a user asks in plain English for a dashboard, report, or set of visuals without providing structured input. It introspects the data source, runs two explicit user-confirmation gates (data-model readiness and scaffold readiness), then orchestrates data-source-connector, query-to-pbip, theme-branding, and bi-dash-creator to produce the final dashboard.
---

# NLQ Dashboard Orchestrator

This skill is the front door of the toolkit. It accepts free-form natural language (e.g., "Build me a sales performance dashboard from my Excel file" or "Show monthly revenue and top customers using our Snowflake warehouse") and drives the entire pipeline to a finished PBIP dashboard.

## When to Use This Skill

- The user describes a dashboard, report, or set of visuals in natural language
- No structured YAML / SQL / data-model.json is provided up front
- The agent needs to coordinate `data-source-connector`, `query-to-pbip`, `theme-branding`, and `bi-dash-creator`
- An explicit, gated, confirmation-driven workflow is required

## Pipeline Stages

```text
┌──────────────────────────────────────────────────────────────────┐
│ 0. Capture NLQ intent                                            │
│ 1. data-source-connector → data-model.json                       │
│ 2. GATE A: confirm data model readiness with the user            │
│ 3. NLQ Q&A loop: visuals, fields, filters, layout                │
│ 4. GATE B: confirm scaffold readiness with the user              │
│ 5. For each visual: run query-to-pbip pipeline                   │
│ 6. theme-branding → apply theme                                  │
│ 7. bi-dash-creator → compose multi-visual dashboard              │
│ 8. Deliver zipped PBIP + summary                                 │
└──────────────────────────────────────────────────────────────────┘
```

## Stage 0: Capture NLQ Intent

Extract the following from the user's free-form request:

- **Dashboard theme / topic** (e.g., "sales performance", "delivery operations")
- **Data source hint** (e.g., "Excel file", "our Databricks warehouse", "the orders database")
- **Implicit visual count** (e.g., "trend, top 5, total" suggests 3 visuals)
- **Time scope** (e.g., "last 12 months", "year-to-date", "2024")
- **Audience cues** (executive, operational, analytical)

If the data source is not mentioned, ask: *"Where does the data live? (database, cloud warehouse, Excel/CSV file, API, etc.)"*

## Stage 1: Invoke data-source-connector

Delegate to the `data-source-connector` skill with the source hint. Expected output:

- `data-model.json` describing tables, columns, types, primary/foreign keys, sample rows
- A list of **open questions** the connector could not resolve automatically

If the connector returns open questions, surface them verbatim to the user. Do not proceed to Gate A until all open questions are answered.

## Stage 2: GATE A — Data Model Readiness

**This gate is mandatory.** Before any modeling work begins, summarize the discovered (or user-described) data model and ask for confirmation.

Present a structured summary:

```text
Data Model Summary
──────────────────
Source:         <connection or file path>
Tables:         <N> tables discovered
  • fact_sales (12 cols, ~50k rows) — grain: order line
  • dim_customer (8 cols)
  • dim_date (15 cols)
Relationships:  3 inferred
  • fact_sales.customer_key → dim_customer.customer_key
  • fact_sales.order_date_key → dim_date.date_key
  • fact_sales.product_key → dim_product.product_key
Date dimension: dim_date (date, year, month, quarter columns present)
Open questions:
  1. Is `dim_product` needed for this dashboard?
  2. Should `order_date_key` or `delivered_date_key` be the default date role?
```

Then ask explicitly: *"Does this data model look right? Should I add, remove, or rename anything before continuing?"*

**Blocking rule:** do NOT progress to Stage 3 until the user confirms the data model. If the user reports missing tables, ambiguous grain, or unclear relationships, loop back to `data-source-connector` for re-introspection or accept user-provided corrections to `data-model.json`.

## Stage 3: NLQ Q&A Loop

For each visual implied by the request, iteratively clarify:

| Question Type | Example |
|---|---|
| Visual count | "How many visuals do you want on the dashboard? (default: 4 — trend, top-N, KPI, breakdown)" |
| Measure | "Which measure should the KPI card show — total revenue, total orders, or both?" |
| Dimension | "Should the trend be by month or by day?" |
| Filter | "Any default filters (region, year, status)?" |
| Layout | "Standard 2x2 grid, or do you want a hero KPI row on top?" |
| Theme | "Corporate, modern, minimal, or dark theme?" |

Track all answers in a **Dashboard Plan** internal structure:

```json
{
  "dashboardName": "SalesPerformance",
  "theme": "corporate",
  "layout": "2x2-grid",
  "visuals": [
    { "id": "v1", "intent": "total revenue KPI", "type": "cardVisual", "measure": "Total Revenue", "filters": [] },
    { "id": "v2", "intent": "monthly revenue trend", "type": "lineChart", "category": "dim_date.month", "y": "Total Revenue" },
    { "id": "v3", "intent": "top 10 customers", "type": "clusteredBarChart", "category": "dim_customer.name", "y": "Total Revenue", "topN": 10 },
    { "id": "v4", "intent": "revenue by region", "type": "filledMap", "category": "dim_customer.region", "size": "Total Revenue" }
  ]
}
```

Use `visual-selector` rules to suggest defaults when the user is unsure.

## Stage 4: GATE B — Scaffold Readiness

**This gate is mandatory.** Before any file generation, present the full Dashboard Plan and ask for explicit confirmation.

Present the plan:

```text
Dashboard Plan
──────────────
Name:    SalesPerformance
Theme:   corporate
Layout:  2x2 grid on a single 1280x720 page

Visual 1 (top-left)    — Card: Total Revenue
Visual 2 (top-right)   — Line Chart: Total Revenue by Month
Visual 3 (bottom-left) — Clustered Bar: Top 10 Customers by Revenue
Visual 4 (bottom-right)— Filled Map: Revenue by Region

All visuals share the dim_date filter context (default: last 12 months).
```

Then ask **verbatim**: *"Are you done with clarifications and ready to scaffold all visuals into the final dashboard? (yes / no — let me know if anything should change)"*

**Blocking rule:** do NOT progress to Stage 5 until the user answers *yes* (or equivalent affirmative). If the user wants changes, loop back to Stage 3.

## Stage 5: Run query-to-pbip per Visual

For each visual in the confirmed Dashboard Plan:

1. Pass the visual's spec + `data-model.json` to `query-to-pbip`
2. `query-to-pbip` runs its four stages (semantic-mapper → visual-selector → visual-generator → project-packager)
3. Output lands in `generated-reports/<VisualName>/`

Use `--repo-root` when scaffolding so the SemanticModel is shared across visuals (avoids duplicating TMDL per visual).

## Stage 6: Apply Theme

Delegate to `theme-branding`:

- Theme name from the Dashboard Plan (corporate / modern / minimal / dark, or a custom theme)
- Copies the theme JSON into `<ProjectName>.Report/StaticResources/SharedResources/BaseThemes/`
- Updates `report.json` `themeCollection` accordingly

## Stage 7: Compose Final Dashboard

Delegate to `bi-dash-creator` with the list of generated report names. This skill:

- Validates semantic-model consistency across reports
- Filters excluded visual types (cards/slicers/kpis stay; the rest go on the dashboard)
- Assigns 2x2 grid positions (or honors a custom layout from Stage 3)
- Outputs `generated-dashboards/<DashboardName>Dash/`

## Stage 8: Deliver

Provide the user with:

- Path to the zipped PBIP
- Summary of generated artifacts (tables, measures, visuals, theme)
- Open-in-Power-BI-Desktop instructions

## Error Handling

| Failure | Recovery |
|---|---|
| `data-source-connector` cannot reach the source | Ask user for credentials / file path; do not proceed past Stage 1 |
| User cannot confirm data model (Gate A) | Loop back to Stage 1 with corrections |
| Visual spec references a field not in `data-model.json` | Ask user to map to an existing field or add the field via Stage 1 |
| User declines at Gate B | Loop back to Stage 3 |
| `query-to-pbip` fails on a visual | Report which visual failed; ask user whether to skip, fix, or abort |
| Theme application fails | Fall back to default `CY25SU11` theme and warn the user |

## Resources

- **`references/clarification-prompts.md`** — Standard question bank for the NLQ Q&A loop
- **`references/dashboard-plan-schema.md`** — JSON schema for the internal Dashboard Plan
- **`references/example-flows.md`** — Worked end-to-end examples (Excel, Databricks, SQL Server)

## Cross-Skill References

| Stage | Skill |
|---|---|
| Stage 1 | `data-source-connector` |
| Stages 5 | `query-to-pbip` (which internally uses `semantic-mapper`, `visual-selector`, `visual-generator`, `project-packager`) |
| Stage 6 | `theme-branding` |
| Stage 7 | `bi-dash-creator` |
