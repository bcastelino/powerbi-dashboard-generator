# Visual Selection Rules Reference

Detailed decision tree and examples for selecting the optimal Power BI visual type based on query characteristics. Use this document when executing the visual-selector sub-skill (Stage 2).

## Decision Tree

### Step 1: Count Measures and Dimensions

From the query, count:
- **Measures**: Aggregated values (SUM, COUNT, AVG, etc.)
- **Dimensions**: Grouping/slicing columns (categorical, temporal, geographic)

### Step 2: Classify Dimensions

For each dimension, determine its type:

**Temporal indicators:**
- Column name: `date`, `month`, `year`, `quarter`, `time`, `period`, `week`
- Source table: `dim_date`, `dim_date_delivery`, or any date dimension
- Data type: `dateTime` in TMDL

**Geographic indicators:**
- Column name: `state`, `city`, `country`, `region`, `zip`, `postal`, `latitude`, `longitude`, `geo`
- Presence of geographic hierarchy (state > city)

**Nominal/Categorical (default):**
- Everything else: `category_name`, `product_id`, `seller_id`, `payment_type`

### Step 3: Apply Selection Matrix

| Measures | Dimensions | Dim Type | Visual | Example Query |
|---|---|---|---|---|
| 1 | 0 | - | `cardVisual` | "What is total revenue?" |
| 2-4 | 0 | - | `cardVisual` (multi-row) | "Show revenue, AOV, and order count" |
| 5+ | 0 | - | `tableEx` | "Show all KPIs" |
| 1 | 1 | Temporal | `lineChart` | "Revenue by month" |
| 1 | 1 | Nominal | `clusteredColumnChart` | "Revenue by state" |
| 1 | 1 | Geographic | `filledMap` | "Revenue by state on map" |
| 2+ | 1 | Temporal | `lineChart` | "Revenue and orders by month" |
| 2+ | 1 | Nominal | `clusteredBarChart` | "Compare revenue and freight by category" |
| 1 | 2 | Both Nominal | `pivotTable` | "Revenue by state and category" |
| 1 | 2 | Temporal + Nominal | `lineChart` (series) | "Revenue by month, split by category" |
| Any | 3+ | Any | `tableEx` | "Detailed breakdown with many columns" |

### Derived Field Routing

When Stage 1 provides derived fields (SQL aliases materialized in TMDL), apply these defaults:

- Derived categorical or binary fields -> `Series` for chart visuals to enable legend color splits.
- Derived temporal fields -> `Category` for trend visuals.
- Derived numeric aggregate fields -> value buckets (`Y`, `Values`, `Size`).
- For `tableEx` and `pivotTable`, include derived fields as visible data fields.

### Step 4: Check for Override Signals

Some query patterns override the default selection:

| Signal | Override To | Example |
|---|---|---|
| Query asks for "trend" or "over time" | `lineChart` | "Revenue trend over time" |
| Query asks for "compare" or "comparison" | `clusteredBarChart` | "Compare states" |
| Query asks for "top N" or "ranking" | `clusteredColumnChart` (sorted) | "Top 10 products" |
| Query asks for "breakdown" or "distribution" | `pieChart` | "Revenue breakdown by category" |
| Query asks for "detail" or "list" | `tableEx` | "Show order details" |
| Query asks for "filter" or "slicer" | Add `slicer` visual | "Add a date filter" |

## Multi-Row Card Configuration

When multiple measures with no dimensions are selected, use the card visual with multi-row layout:

- Up to 4 measures: Use individual `cardVisual` visuals in a row (Header layout from `layout-patterns.md`)
- 5+ measures: Fall back to `tableEx`

## Visual Type to PBIR `visualType` Mapping

| Friendly Name | PBIR `visualType` Value |
|---|---|
| Card | `cardVisual` |
| Clustered Column Chart | `clusteredColumnChart` |
| Clustered Bar Chart | `clusteredBarChart` |
| Line Chart | `lineChart` |
| Table | `tableEx` |
| Matrix | `pivotTable` |
| Slicer | `slicer` |
| Map (Filled) | `filledMap` |
| Map (Bubble) | `azureMap` |
| Pie Chart | `pieChart` |
| Donut Chart | `donutChart` |
| Scatter Chart | `scatterChart` |

## Example Walkthroughs

### Example 1: "Show me total revenue"

1. Measures: 1 (`Total Revenue (GMV)`)
2. Dimensions: 0
3. Selection: `cardVisual`
4. Bucket mapping: `Values: [Total Revenue (GMV)]`

### Example 2: "Revenue by state"

1. Measures: 1 (`Total Revenue (GMV)`)
2. Dimensions: 1 (`customer_state` from `dim_customer`)
3. Dimension type: Geographic -> but for chart, treat as Nominal
4. Selection: `clusteredColumnChart`
5. Bucket mapping: `Category: [customer_state], Y: [Total Revenue (GMV)]`

### Example 3: "Monthly revenue trend"

1. Measures: 1 (`Total Revenue (GMV)`)
2. Dimensions: 1 (`month` from `dim_date`)
3. Dimension type: Temporal
4. Selection: `lineChart`
5. Bucket mapping: `Category: [month], Y: [Total Revenue (GMV)]`

### Example 4: "Revenue and order count by category over time"

1. Measures: 2 (`Total Revenue (GMV)`, `Total Orders`)
2. Dimensions: 2 (`month` Temporal, `category_name` Nominal)
3. Primary dimension: Temporal -> `lineChart`
4. Second dimension becomes series
5. Selection: `lineChart` with series
6. Bucket mapping: `Category: [month], Y: [Total Revenue (GMV), Total Orders], Series: [category_name]`

### Example 5: "Revenue by state and product category"

1. Measures: 1 (`Total Revenue (GMV)`)
2. Dimensions: 2 (`customer_state` Nominal, `category_name` Nominal)
3. Both Nominal -> `pivotTable`
4. Selection: `pivotTable`
5. Bucket mapping: `Rows: [customer_state], Columns: [category_name], Values: [Total Revenue (GMV)]`
