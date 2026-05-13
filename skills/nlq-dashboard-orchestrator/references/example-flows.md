# Example Flows

End-to-end worked examples showing the orchestrator behavior with different sources.

## Example 1: Excel File

**User:** "Build me a sales dashboard from `C:\data\sales.xlsx`."

**Agent flow:**

1. **Stage 0:** Detects file path; topic = "sales dashboard"
2. **Stage 1:** Invokes `data-source-connector` with `type=excel`, `path=C:\data\sales.xlsx`
3. Connector returns `data-model.json` with 3 sheets (Orders, Customers, Products) and inferred relationships
4. **Stage 2 (Gate A):** Presents summary; user confirms
5. **Stage 3:** Q&A — user asks for 4 visuals: revenue KPI, monthly trend, top customers, revenue by product category
6. **Stage 4 (Gate B):** Plan summary; user says "yes"
7. **Stage 5–7:** Pipeline runs; theme applied; dashboard composed
8. **Stage 8:** Delivers `generated-dashboards/SalesDash/SalesDash.zip`

## Example 2: Databricks

**User:** "Show monthly revenue and top-10 sellers for 2024 from our Databricks olist warehouse."

**Agent flow:**

1. **Stage 0:** Detects Databricks; year filter = 2024
2. **Stage 1:** Invokes `data-source-connector` with `type=databricks`. Connector asks for workspace hostname + SQL warehouse ID. User provides.
3. Connector returns `data-model.json` with `wl_internal.olist_ecommerce` tables
4. **Stage 2 (Gate A):** User confirms
5. **Stage 3:** Q&A — 2 visuals confirmed: line chart (monthly revenue 2024) + clustered bar (top 10 sellers)
6. **Stage 4 (Gate B):** User confirms
7. **Stages 5–7:** Pipeline → theme → dashboard
8. **Stage 8:** Delivers `generated-dashboards/OlistRevenueDash/`

## Example 3: User reports missing table at Gate A

**User:** "Build me a delivery operations dashboard from the warehouse."

**Stage 2 (Gate A):** Agent presents summary including `dim_date` but not `dim_date_delivery`.

**User:** "I need delivery date as a separate role — orders use `purchase_date_key`, deliveries use `delivered_date_key`."

**Agent:**

- Loops back to Stage 1
- Re-invokes `data-source-connector` with hint to materialize `dim_date_delivery` as a role-playing date table
- Re-presents updated data model at Gate A
- Only proceeds when user confirms

## Example 4: User declines at Gate B

**Stage 4 (Gate B):** Agent presents plan with `Top 5 Customers` bar chart.

**User:** "Make it top 10 and add a slicer for region."

**Agent:**

- Updates the Dashboard Plan: `topN: 10`, adds a `slicer` visual on `dim_customer.region`
- Re-presents the updated plan
- Asks the Gate B question again
- Proceeds only on explicit "yes"
