# Dashboard Layout Rules

## Page Dimensions

- **Width**: 1280 pixels
- **Height**: 720 pixels
- **Display Option**: FitToPage

## 2x2 Quadrant Grid

All visuals are arranged in an edge-to-edge 2x2 grid with no margins or gaps. Each quadrant is exactly 640x360 pixels.

### Position Table

| Position | x | y | width | height | z | tabOrder |
|---|---|---|---|---|---|---|
| Top-Left | 0 | 0 | 640 | 360 | 0 | 0 |
| Top-Right | 640 | 0 | 640 | 360 | 1 | 1000 |
| Bottom-Left | 0 | 360 | 640 | 360 | 2 | 2000 |
| Bottom-Right | 640 | 360 | 640 | 360 | 3 | 3000 |

## Pagination Rules

- **Maximum 4 visuals per page**
- If more than 4 visuals are selected, additional pages are created
- Each new page follows the same 2x2 grid layout
- Pages are named sequentially: "Page 1", "Page 2", etc.

## Visual Schema Version

All visuals in the dashboard use schema version **2.6.0**:

```
https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.6.0/schema.json
```

## Excluded Visual Types

The following visual types are excluded from dashboards:

- `cardVisual` - Summary cards are not suitable for dashboard grids
- `slicer` - Filter slicers should not be placed in dashboard quadrants
- `kpi` - KPI indicators are excluded from the grid layout
