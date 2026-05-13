---
name: visual-selector
description: Determines the best Power BI visual type based on the measures and dimensions in a query. Use this skill when deciding which chart or visual to generate for a given data profile (e.g., cardVisual for single KPIs, lineChart for time series, clusteredColumnChart for categorical comparisons). This is Stage 2 of the query-to-pbip pipeline.
---

# Visual Selector

Determine the optimal Power BI visual type for a given query based on the number and classification of measures and dimensions. This skill analyzes the data profile from the semantic mapper output and produces a visual type recommendation with field-to-bucket mappings.

## When to Use This Skill

- Choosing the best visual type for a Genie query result
- Mapping measures and dimensions to visual data buckets (Category, Y, Data, Values, etc.)
- Selecting chart types as part of the query-to-pbip pipeline (Stage 2)
- Recommending page layouts based on visual type

## Inputs

- **Measures** — List of measure names, data types, and format types from Stage 1
- **Dimensions** — List of dimension names, source tables, and data types from Stage 1
- **Derived fields** — SQL aliases materialized in Stage 1 as calculated columns or measures
- **Query intent** (optional) — Original natural language query for override signal detection

## Outputs

- `visualType` — The PBIR visual type string (e.g., `cardVisual`, `clusteredColumnChart`, `lineChart`)
- `bucketMapping` — Which fields go into which visual data buckets
- `layoutPosition` — Recommended position coordinates for the visual

## Visual Selection Decision Tree

The selection rules below serve as defaults. The agent has the flexibility to decide the best way to display any visual by utilizing the available tables, models, and relationships from the semantic model. When the semantic model provides sort columns, hierarchies, or other metadata that informs a better display choice, the agent should leverage that information rather than rigidly following the decision tree.

### Step 1: Count Measures and Dimensions

From the semantic mapper output, count:

- **Measures**: Aggregated values (SUM, COUNT, AVG, etc.)
- **Dimensions**: Grouping/slicing columns

### Step 2: Classify Each Dimension

| Indicator | Classification | Examples |
|---|---|---|
| Name contains `date`, `month`, `year`, `quarter`, `time` | Temporal | `order_date`, `Month` |
| Name contains `state`, `city`, `country`, `region`, `zip` | Geographic | `customer_state`, `Region` |
| Source table is `dim_date`, `dim_date_delivery`, or another date dimension | Temporal | Any role-playing date column |
| All other columns | Nominal | `category_name`, `seller_id` |

**Derived field classification defaults:**

- Derived text/binary aliases (`CASE`, bucketing labels, flags) => Nominal
- Derived date/time aliases (`DATE_TRUNC`, period buckets) => Temporal
- Derived numeric aggregates/ratios => Measure

**Role-specific temporal routing:**

- Purchase/order trends default to `dim_date`
- Delivery/shipping/fulfilled trends default to the matching role-playing date table (for example `dim_date_delivery`)
- If the measure compares two dates but the query says "by delivery month", use the delivery date role for Category and filters
- If the measure compares two dates but the query says "by purchase month" or just "monthly orders/revenue", use `dim_date`

### Step 3: Apply the Selection Matrix

| Measures | Dimensions | Dimension Type | Visual Type |
|---|---|---|---|
| 1 | 0 | — | `cardVisual` |
| 2–4 | 0 | — | `cardVisual` (one per measure, row layout) |
| 5+ | 0 | — | `tableEx` |
| 1 | 1 | Temporal | `lineChart` |
| 1 | 1 | Nominal | `clusteredColumnChart` |
| 1 | 1 | Geographic | `filledMap` |
| 2+ | 1 | Temporal | `lineChart` |
| 2+ | 1 | Nominal | `clusteredBarChart` |
| 2 | 1 | Nominal + "scatter"/"correlation" keywords | `scatter-bubble-chart` (secondary) |
| 3 | 1 | Nominal + "bubble" keyword | `scatter-bubble-chart` with size (secondary) |
| 2–4 | 1 | Nominal | `clustered-column-multi-measure` (secondary, alternative to `clusteredBarChart`) |
| 2+ | 1 | Temporal | `line-chart-multi-y` (secondary, alternative to `lineChart`) |
| 1 | 2 | Both Nominal | `pivotTable` (matrix) |
| 1 | 2 | Temporal + Nominal | `lineChart` with Series |
| Any | 3+ | Any | `tableEx` |

### Step 4: Check for Override Signals

Scan the original query text for keywords that override the default selection:

| Signal Words | Override To |
|---|---|
| "trend", "over time", "timeline" | `lineChart` |
| "compare", "comparison", "versus" | `clusteredBarChart` |
| "top N", "ranking", "rank" | `clusteredColumnChart` (sorted desc) |
| "breakdown", "distribution", "share" | `pieChart` |
| "detail", "list", "all records" | `tableEx` |
| "filter", "slicer", "select" | Add companion `slicer` visual |
| "map", "geographic", "location" | `filledMap` |
| "scatter", "correlation", "relationship" | `scatter-bubble-chart` |
| "bubble" | `scatter-bubble-chart` |
| "donut" | `donutChart` |
| "gradient", "heatmap" (when geographic dimension present) | `azure-map-gradient` |
| "range", "between" (when date dimension present) | `slicer-between-date` |
| "last N months", "past N months", "last N days" | Keep temporal chart/slicer choice and add current-date-relative filter intent |
| "latest N months in the data", "most recent N months in data" | Keep temporal chart/slicer choice and add data-anchored filter intent |
| "dropdown" (when slicer context) | `slicer-dropdown` |
| "multiselect", "multiple" (when slicer context) | `slicer-list-multiselect` |

### Step 5: Apply Derived Field Routing Rules

When derived fields are available from Stage 1, map them using these defaults:

- If a derived **categorical** field exists and chart already has a primary category axis, place the derived field in `Series` (legend/color split).
- If a derived **binary flag** exists (for example `Top Flag`), prioritize `Series` mapping over replacing the main category.
- If a derived **temporal** field exists, prefer it for `Category` on trend visuals.
- If a derived **numeric aggregate/ratio** exists, map it to value buckets (`Y`, `Values`, `Size`) as a measure.
- For `tableEx` and `pivotTable`, include derived fields as explicit columns/rows/values rather than legend-only metadata.

## Query Bucket Mapping

After selecting the visual type, map fields to the correct data buckets:

### cardVisual

```json
{
  "Data": ["<measure>"]
}
```

### clusteredColumnChart / clusteredBarChart

```json
{
  "Category": ["<dimension>"],
  "Y": ["<measure1>", "<measure2>"],
  "Series": ["<optional_derived_categorical_dimension>"]
}
```

### lineChart

```json
{
  "Category": ["<temporal_dimension>"],
  "Y": ["<measure>"],
  "Series": ["<optional_nominal_dimension>"]
}
```

### lineClusteredColumnComboChart

```json
{
  "Category": ["<temporal_dimension>"],
  "Y": ["<primary_measure>"],
  "Y2": ["<secondary_measure>"]
}
```

### tableEx

```json
{
  "Values": ["<dim1>", "<dim2>", "<measure1>", "<measure2>"]
}
```

### pivotTable (matrix)

```json
{
  "Rows": ["<dimension1>"],
  "Columns": ["<dimension2>"],
  "Values": ["<measure>"]
}
```

### slicer

```json
{
  "Values": ["<dimension>"]
}
```

### filledMap

```json
{
  "Category": ["<geographic_dimension>"],
  "Size": ["<measure>"]
}
```

### scatter-bubble-chart

```json
{
  "X": ["<x_measure>"],
  "Y": ["<y_measure>"],
  "Details": ["<category_dimension>"],
  "Size": ["<optional_size_measure>"]
}
```

### azure-map-gradient

```json
{
  "Location": ["<geographic_dimension>"],
  "Gradient": ["<measure>"]
}
```

### azure-map-bubble

```json
{
  "Location": ["<geographic_dimension>"],
  "Size": ["<measure>"]
}
```

### slicer-between-date

```json
{
  "Values": ["<date_dimension>"]
}
```

### slicer-dropdown

```json
{
  "Values": ["<dimension>"]
}
```

### slicer-list-multiselect

```json
{
  "Values": ["<dimension>"]
}
```

## Visual Type to PBIR Type Mapping

| Display Name | PBIR `visualType` | Data Bucket(s) |
|---|---|---|
| Card (new) | `cardVisual` | `Data` |
| Clustered Column Chart | `clusteredColumnChart` | `Category`, `Y` |
| Clustered Bar Chart | `clusteredBarChart` | `Category`, `Y`, `Series` |
| Line Chart | `lineChart` | `Category`, `Y`, `Series` |
| Combo Chart | `lineClusteredColumnComboChart` | `Category`, `Y`, `Y2` |
| Table | `tableEx` | `Values` |
| Matrix | `pivotTable` | `Rows`, `Columns`, `Values` |
| Slicer | `slicer` | `Values` |
| Filled Map | `filledMap` | `Category`, `Size` |
| Pie Chart | `pieChart` | `Category`, `Y` |
| Donut Chart | `donutChart` | `Category`, `Y` |
| Scatter/Bubble Chart | `scatterChart` | `X`, `Y`, `Details`, `Size` |
| Azure Map (Gradient) | `azureMap` | `Location`, `Gradient` |
| Azure Map (Bubble) | `azureMap` | `Location`, `Size` |
| Line Chart (Multi-Y) | `lineChart` | `Category`, `Y` (multiple measures) |
| Clustered Column (Multi-Measure) | `clusteredColumnChart` | `Category`, `Y` (multiple measures) |
| Matrix (Basic) | `pivotTable` | `Rows`, `Columns`, `Values` |
| Slicer (Date Range) | `slicer` | `Values` |
| Slicer (Dropdown) | `slicer` | `Values` |
| Slicer (Multi-select) | `slicer` | `Values` |

## Template Source Priority

The visual-selector references templates from two sources with the following priority:

1. **Primary**: `skills/query-to-pbip/assets/visual-templates/` - These templates are checked first
2. **Secondary**: cn-dataworks-pbir-visuals research templates - Used when primary templates don't cover the use case

When multiple visual types could satisfy the same query pattern, prefer the primary source template. Secondary templates are used for specialized visualizations not available in the primary set (e.g., scatter plots, Azure maps, enhanced slicers).

## Layout Recommendations

| Visual Type | Recommended Layout | Position |
|---|---|---|
| Single `cardVisual` | Centered | x:440, y:260, w:400, h:200 |
| Multi `cardVisual` (2–4) | Header row | x:20/340/660/980, y:20, w:300, h:150 |
| `clusteredColumnChart` / `lineChart` | Full page | x:20, y:20, w:1240, h:680 |
| `tableEx` / `pivotTable` | Full page | x:20, y:20, w:1240, h:680 |
| Chart + `slicer` | Slicer corner, chart main | Slicer: x:0, y:0, w:110, h:110; Chart: x:110, w:1170 |

## Example Walkthroughs

### "What is total revenue?"

- Measures: 1 (Total Revenue)
- Dimensions: 0
- Result: `cardVisual`, Data: [Total Revenue]

### "Revenue by state"

- Measures: 1 (Total Revenue)
- Dimensions: 1 (customer_state → Nominal)
- Result: `clusteredColumnChart`, Category: [customer_state], Y: [Total Revenue]

### "Units sold by category with top flag"

- Measures: 1 (`Units Sold`)
- Dimensions: 2 (`category_name`, derived `Top Flag`)
- Result: `clusteredBarChart`
- Bucket mapping: `Category: [category_name], Y: [Units Sold], Series: [Top Flag]`

### "Monthly revenue trend"

- Measures: 1 (Total Revenue)
- Dimensions: 1 (month → Temporal)
- Result: `lineChart`, Category: [month], Y: [Total Revenue]

### "Revenue and rolling revenue by month"

- Measures: 2 (Total Revenue, Rolling 1 Month)
- Dimensions: 1 (month_name → Temporal)
- Result: `lineClusteredColumnComboChart`, Category: [month_name], Y: [Total Revenue], Y2: [Rolling 1 Month]

### "Average delivery time by delivery month for the latest 12 months in the data"

- Measures: 1 (`Avg Delivery Time`)
- Dimensions: 1 (`dim_date_delivery` month/date → Temporal)
- Filter intent: data-anchored last 12 months
- Result: `lineChart`, Category: [`dim_date_delivery` month hierarchy], Y: [`Avg Delivery Time`]

### "Average delivery time trend for the last 12 months"

- Measures: 1 (`Avg Delivery Time`)
- Dimensions: 1 (temporal)
- Filter intent: current-date-relative last 12 months
- Result: `lineChart`, Category aligned to the requested business timeline, Y: [`Avg Delivery Time`]

### "Revenue by state and category"

- Measures: 1 (Total Revenue)
- Dimensions: 2 (customer_state → Nominal, category_name → Nominal)
- Result: `pivotTable`, Rows: [customer_state], Columns: [category_name], Values: [Total Revenue]

## Error Handling

| Situation | Resolution |
|---|---|
| No measures found | Default to `tableEx` showing all available dimensions |
| Ambiguous dimension type | Default to Nominal |
| Conflicting override signals | Use the first matched signal |
| Too many measures for card layout (5+) | Fall back to `tableEx` |

## Reference Templates

Before constructing a `visual.json` output, consult the template files in `skills/visual-selector/references/`. Each template provides a complete worked example showing a user question, the corresponding Genie SQL query, and the full `visual.json` output. Use these templates as learning material to inform decisions about visual type selection, field-to-bucket mappings, formatting options, sorting configuration, and filter application.

When building a `visual.json`, find the reference template that most closely matches the target visual type and follow its patterns for:

- **Query structure** — How `queryState` buckets (Category, Series, Y, Tooltips) are populated with field projections
- **Sort definitions** — How `sortDefinition` is configured for the visual type
- **Object formatting** — How `objects` properties (axis settings, labels, legends, gridlines, markers) are set
- **Visual container objects** — How titles, backgrounds, borders, and other container-level properties are configured
- **Filter configuration** — How `filterConfig` entries are structured, including TopN subquery filters and Advanced filters

### references/

- `barChart.md` — Bar chart template with Category/Series/Y buckets, categorical axis configuration, and ascending sort
- `lineChart.md` — Line chart template with temporal Category hierarchy, Series dimension, marker/line styles, and TopN filter
- `lineClusteredColumnComboChart.md` — Combo chart template with Y column axis, reference lines (min/max/average/median/percentile), and Advanced measure filters
- `pieChart.md` — Pie chart template with Category/Y buckets, outside label positioning with percent-of-total style, and TopN filter
- `stackedColumnChart.md` — Stacked column chart template with Category hierarchy, Series split, Tooltip measures, and multi-filter configuration
- `clusteredColumnChart.md` — Clustered column chart template with Category/Y buckets, categorical axis configuration, and descending sort
