# Dashboard Plan Schema

The internal data structure assembled during Stage 3 (NLQ Q&A loop) and confirmed at Stage 4 (Gate B). It is the single source of truth handed to `query-to-pbip` for each visual.

## JSON Shape

```json
{
  "dashboardName": "string (PascalCase, no spaces)",
  "description": "string (optional, one-line summary)",
  "theme": "corporate | modern | minimal | dark | <custom-theme-name>",
  "layout": "2x2-grid | hero-kpi-row | custom",
  "pageSize": { "width": 1280, "height": 720 },
  "dataSource": {
    "type": "databricks | snowflake | sqlserver | postgres | mysql | bigquery | excel | csv | odata | sharepoint",
    "connection": "<connection-details-or-file-path>",
    "dataModelPath": "<path-to-data-model.json>"
  },
  "visuals": [
    {
      "id": "v1",
      "intent": "human-readable purpose",
      "type": "cardVisual | clusteredColumnChart | lineChart | clusteredBarChart | tableEx | pivotTable | slicer | filledMap | pieChart | donutChart | scatterChart | lineClusteredColumnComboChart",
      "buckets": {
        "Category": ["dim_date.month"],
        "Y": ["fact_sales.Total Revenue"],
        "Series": []
      },
      "filters": [
        { "field": "dim_date.year", "type": "Categorical", "values": [2024] }
      ],
      "sort": { "field": "fact_sales.Total Revenue", "direction": "Descending" },
      "topN": 10,
      "position": { "x": 0, "y": 0, "width": 640, "height": 360, "z": 0, "tabOrder": 0 }
    }
  ],
  "sharedFilters": [
    { "field": "dim_date.year", "type": "Categorical", "scope": "page" }
  ]
}
```

## Field Reference

| Field | Required | Notes |
|---|---|---|
| `dashboardName` | yes | Used for output folder and `.pbip` filename |
| `theme` | yes | Default `corporate` if user has no preference |
| `layout` | yes | Drives default `position` if not explicit per visual |
| `dataSource.dataModelPath` | yes | Output of `data-source-connector`; consumed by `semantic-mapper` |
| `visuals[].type` | yes | Must map to a PBIR visualType supported by `visual-generator` |
| `visuals[].buckets` | yes | Field-to-bucket mapping per `visual-selector` rules |
| `visuals[].filters` | no | Per-visual filterConfig |
| `visuals[].position` | no | If absent, populated by `bi-dash-creator` from the layout template |
| `sharedFilters` | no | Page-level filters applied across all visuals |

## Validation Rules

Before Gate B, ensure:

1. Every `visuals[].buckets` field reference exists in `data-model.json` (table + column/measure)
2. Every `visuals[].type` is one of the supported PBIR types
3. `visuals[].topN` only set on chart types that support sorted truncation
4. `dataSource.dataModelPath` file exists and is non-empty
5. `dashboardName` matches `^[A-Z][A-Za-z0-9]*$` (PascalCase, no spaces, no leading digit)
