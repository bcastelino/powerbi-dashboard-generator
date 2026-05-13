---
name: visual-generator
description: Builds Power BI report visual JSON files in PBIR format, where each visual is a separate visual.json file inside its own directory. Also generates page.json, pages.json, report.json, version.json, and definition.pbir. Use this skill when generating the report layer of a PBIP project from a selected visual type and field mappings. This is Stage 3 of the query-to-pbip pipeline.
---

# Visual Generator

Build Power BI report visual definitions in PBIR (Power BI Enhanced Report) format. In PBIR, each visual is stored as a separate `visual.json` file inside its own directory under `pages/<pageId>/visuals/<visualId>/`. This skill takes a visual type and field-to-bucket mapping from the visual selector and produces all report files.

## When to Use This Skill

- Generating individual `visual.json` files for a PBIP report
- Building visual containers with semantic query bindings
- Creating report definition files (report.json, version.json, pages.json)
- Producing `definition.pbir` pointer files linking report to semantic model
- Constructing visuals as part of the query-to-pbip pipeline (Stage 3)

## Inputs

- **visualType** — The PBIR visual type string from Stage 2 (e.g., `cardVisual`, `clusteredColumnChart`)
- **bucketMapping** — Field-to-bucket assignments from Stage 2
- **tableNames** — Table and column/measure names from Stage 1
- **projectName** — Name of the PBIP project (for definition.pbir path references)
- **pageLayout** (optional) — Page dimensions; defaults to 1280x720

## Outputs

| File | Location | Purpose |
|---|---|---|
| `visual.json` | `definition/pages/<pageId>/visuals/<visualId>/` | One file per visual (schema 2.5.0) |
| `page.json` | `definition/pages/<pageId>/` | Page definition (schema 2.0.0) |
| `pages.json` | `definition/pages/` | Page ordering metadata |
| `report.json` | `definition/` | Report-level configuration (schema 3.1.0) |
| `version.json` | `definition/` | Report format version |
| `definition.pbir` | `<ProjectName>.Report/` | Pointer to semantic model |

## Visual Generation Workflow

### Step 1: Build the Semantic Query

For each field in the bucket mapping, construct the appropriate field reference. The agent should use the available tables, models, and relationships from Stage 1 to determine the best way to display the visual — leveraging actual column types, sort orders, and relationships defined in the semantic model.

**Column reference** (for dimensions):

```json
{
  "field": {
    "Column": {
      "Expression": { "SourceRef": { "Entity": "<TableName>" } },
      "Property": "<ColumnName>"
    }
  },
  "queryRef": "<TableName>.<ColumnName>",
  "nativeQueryRef": "<ColumnName>",
  "active": true
}
```

**Measure reference** (for aggregated values):

```json
{
  "field": {
    "Measure": {
      "Expression": { "SourceRef": { "Entity": "<FactTableName>" } },
      "Property": "<MeasureName>"
    }
  },
  "queryRef": "<FactTableName>.<MeasureName>",
  "nativeQueryRef": "<MeasureName>"
}
```

The `nativeQueryRef` is typically just the column or measure name without the table prefix.

### Step 2: Select and Populate the Visual Template

Load the appropriate template from `assets/visual-templates/` in the query-to-pbip skill and replace placeholders:

| Template | Visual Type | Placeholders |
|---|---|---|
| `cardVisual.json` | `cardVisual` | `{{VisualName}}`, `{{MeasureTable}}`, `{{MeasureName}}` |
| `clusteredColumnChart.json` | `clusteredColumnChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}`, optional `{{SeriesTable}}`, `{{SeriesColumn}}` |
| `clusteredBarChart.json` | `clusteredBarChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}`, optional `{{SeriesTable}}`, `{{SeriesColumn}}` |
| `lineChart.json` | `lineChart` | `{{VisualName}}`, `{{CategoryTable}}`, `{{CategoryColumn}}`, `{{MeasureTable}}`, `{{MeasureName}}` |
| `tableEx.json` | `tableEx` | `{{VisualName}}`, `{{Columns}}` |
| `slicer.json` | `slicer` | `{{VisualName}}`, `{{SlicerTable}}`, `{{SlicerColumn}}` |

Replace `{{VisualName}}` with a 20-character hex identifier (e.g., `uuid.uuid4().hex[:20]`).

When Stage 1 includes derived categorical aliases (for example a SQL `CASE` alias), populate the `Series` bucket for supported visuals (`clusteredColumnChart`, `clusteredBarChart`, `lineChart`) so Power BI renders legend-based color splits.

### Step 3: Set Visual Positioning

Apply position coordinates within the `visual.json`:

**Single full-page visual:**

```json
{ "x": 20, "y": 20, "z": 0, "height": 680, "width": 1240, "tabOrder": 0 }
```

**Single centered card:**

```json
{ "x": 440, "y": 260, "z": 0, "height": 200, "width": 400, "tabOrder": 0 }
```

**Multi-card header row (up to 4):**

| Card # | x | y | height | width |
|---|---|---|---|---|
| 1 | 20 | 20 | 150 | 300 |
| 2 | 340 | 20 | 150 | 300 |
| 3 | 660 | 20 | 150 | 300 |
| 4 | 980 | 20 | 150 | 280 |

**Chart with slicer:**

| Element | x | y | height | width | z | tabOrder |
|---|---|---|---|---|---|---|
| Slicer | 0 | 0 | 110 | 110 | 4000 | 4000 |
| Chart | 110 | 0 | 680 | 1170 | 0 | 0 |

### Step 4: Write Each Visual as a Separate File

In PBIR format, each visual gets its own directory and `visual.json` file:

```
definition/pages/<pageId>/visuals/
├── <visualId1>/
│   └── visual.json
├── <visualId2>/
│   └── visual.json
└── <visualId3>/
    └── visual.json
```

Generate a unique 20-character hex ID for each visual: `uuid.uuid4().hex[:20]`

### Step 5: Assemble page.json

The page definition does NOT contain visual definitions (those are in separate files):

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.0.0/schema.json",
  "name": "<pageId>",
  "displayName": "<Page Title>",
  "displayOption": "FitToPage",
  "height": 720,
  "width": 1280
}
```

Set `displayName` to a descriptive title derived from the query (e.g., "Revenue by State").
Generate `name` as a 20-character hex ID: `uuid.uuid4().hex[:20]`

### Step 6: Generate pages.json

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/pagesMetadata/1.0.0/schema.json",
  "pageOrder": ["<pageId>"],
  "activePageName": "<pageId>"
}
```

### Step 7: Generate report.json

Located at `definition/report.json`:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/report/3.1.0/schema.json",
  "themeCollection": {
    "baseTheme": {
      "name": "CY25SU11",
      "reportVersionAtImport": {
        "visual": "2.4.0",
        "report": "3.0.0",
        "page": "2.3.0"
      },
      "type": "SharedResources"
    }
  },
  "resourcePackages": [
    {
      "name": "SharedResources",
      "type": "SharedResources",
      "items": [
        {
          "name": "CY25SU11",
          "path": "BaseThemes/CY25SU11.json",
          "type": "BaseTheme"
        }
      ]
    }
  ],
  "settings": {
    "useStylableVisualContainerHeader": true,
    "exportDataMode": "AllowSummarized",
    "defaultDrillFilterOtherVisuals": true,
    "allowChangeFilterTypes": true,
    "useEnhancedTooltips": true,
    "useDefaultAggregateDisplayName": true
  }
}
```

### Step 8: Generate version.json

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/versionMetadata/1.0.0/schema.json",
  "version": "2.0.0"
}
```

### Step 9: Generate definition.pbir

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definitionProperties/2.0.0/schema.json",
  "version": "4.0",
  "datasetReference": {
    "byPath": {
      "path": "../<ProjectName>.SemanticModel"
    }
  }
}
```

## Visual Container Structure (visual.json)

Every visual uses schema version 2.5.0:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.5.0/schema.json",
  "name": "<20-char-hex-id>",
  "position": {
    "x": 0, "y": 0, "z": 0,
    "height": 0, "width": 0,
    "tabOrder": 0
  },
  "visual": {
    "visualType": "<type>",
    "query": {
      "queryState": {
        "<BucketName>": {
          "projections": [ ... field references ... ]
        }
      },
      "sortDefinition": {
        "sort": [
          {
            "field": { ... field reference (Column or Measure) ... },
            "direction": "Ascending" or "Descending"
          }
        ],
        "isDefaultSort": true
      }
    },
    "drillFilterOtherVisuals": true
  }
}
```

### sortDefinition

The `sortDefinition` object controls the default sort order for the visual. **Always include a `sortDefinition`** in the `visual->query` JSON to improve the visual presentation. The sort field reference uses the same structure as projection field references.

**Sort direction values:** `"Ascending"` or `"Descending"`

**Guidelines for choosing sort:**

- **Line charts with temporal categories** (year, month, date): Sort by the temporal column `Ascending` so data flows chronologically left-to-right. Add both `year` and `month` columns as Category projections when the query involves monthly trends.
- **Column/bar charts with temporal categories**: Sort by the temporal column `Ascending`.
- **Column/bar charts with nominal categories** (state, product, etc.): Sort by the measure `Descending` to show highest values first.
- **Card visuals**: Sort by the measure `Descending`.
- **Table visuals**: Sort by the first measure column `Descending`.

**Example — Line chart with year sort:**

```json
"sortDefinition": {
  "sort": [
    {
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "dim_date" } },
          "Property": "year"
        }
      },
      "direction": "Ascending"
    }
  ],
  "isDefaultSort": true
}
```

**Example — Column chart sorted by measure descending:**

```json
"sortDefinition": {
  "sort": [
    {
      "field": {
        "Measure": {
          "Expression": { "SourceRef": { "Entity": "fact_sales" } },
          "Property": "Total Revenue (GMV)"
        }
      },
      "direction": "Descending"
    }
  ],
  "isDefaultSort": true
}
```

### Temporal Projections for Line Charts

When the genie query involves time-series data (e.g., revenue over time, monthly trends), include multiple temporal columns as Category projections to enable drill-down and proper axis formatting:

```json
"Category": {
  "projections": [
    {
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "dim_date" } },
          "Property": "year"
        }
      },
      "queryRef": "dim_date.year",
      "nativeQueryRef": "year",
      "active": true
    },
    {
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "dim_date" } },
          "Property": "month"
        }
      },
      "queryRef": "dim_date.month",
      "nativeQueryRef": "month",
      "active": true
    }
  ]
}
```

This adds both year and month to the category axis, enabling the user to see monthly breakdowns within each year.

```

## Visual Type to PBIR Mapping

| Display Name | PBIR `visualType` | Data Bucket |
|---|---|---|
| Card (new) | `cardVisual` | `Data` |
| Clustered Column Chart | `clusteredColumnChart` | `Category`, `Y`, `Series` |
| Line Chart | `lineChart` | `Category`, `Y`, `Series` |
| Combo Chart | `lineClusteredColumnComboChart` | `Category`, `Y`, `Y2` |
| Table | `tableEx` | `Values` |
| Matrix | `pivotTable` | `Rows`, `Columns`, `Values` |
| Slicer | `slicer` | `Values` |
| Filled Map | `filledMap` | `Category`, `Size` |
| Pie Chart | `pieChart` | `Category`, `Y` |
| Donut Chart | `donutChart` | `Category`, `Y` |
| Clustered Bar Chart | `clusteredBarChart` | `Category`, `Y`, `Series` |
| Scatter Chart | `scatterChart` | `X`, `Y`, `Size` |

## Z-Order and Tab Order

- Data visuals: z = 0, tabOrder = 0 (increment by 1000 for layering)
- Combo/overlay visuals: z = 3000, tabOrder = 3000
- Slicers: z = 4000, tabOrder = 4000

## Visual Objects Reference

The `visual.objects` property controls formatting and behavior for each visual type. The `visualContainerObjects` property controls container-level formatting (title, background, border) and applies to ALL visual types.

### Value Encoding

All values inside `objects` use expression literals. Encoding rules:

| Type | Encoding | Example |
|---|---|---|
| String | Wrapped in single quotes | `"'Top'"`, `"'Dropdown'"` |
| Number | Suffixed with `D` | `"28D"`, `"0D"` |
| Boolean | Lowercase string | `"true"`, `"false"` |
| Long integer | Suffixed with `L` | `"40L"` |

### General Structure

```json
"objects": {
  "propertyName": [
    {
      "properties": {
        "subProperty": {
          "expr": {
            "Literal": {
              "Value": "'value'"
            }
          }
        }
      }
    }
  ]
}
```

---

### cardVisual

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `labels` | `fontSize` | Number | Font size for the value label (e.g., `"28D"`) |
| `labels` | `labelDisplayUnits` | Number | Display units: `0D` = Auto, `1D` = None, `1000D` = Thousands, `1000000D` = Millions |
| `labels` | `color` | String | Hex color for label text |
| `categoryLabels` | `show` | Boolean | Show/hide category label below the value |
| `categoryLabels` | `fontSize` | Number | Font size for the category label |

**Example — Card with fontSize 28, auto display units:**

```json
"objects": {
  "labels": [
    {
      "properties": {
        "fontSize": {
          "expr": { "Literal": { "Value": "28D" } }
        },
        "labelDisplayUnits": {
          "expr": { "Literal": { "Value": "0D" } }
        }
      }
    }
  ],
  "categoryLabels": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "fontSize": {
          "expr": { "Literal": { "Value": "12D" } }
        }
      }
    }
  ]
}
```

---

### clusteredColumnChart

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `categoryAxis` | `show` | Boolean | Show/hide category axis |
| `categoryAxis` | `labelAngle` | Number | Axis label rotation in degrees |
| `categoryAxis` | `fontSize` | Number | Axis label font size |
| `valueAxis` | `show` | Boolean | Show/hide value axis |
| `valueAxis` | `gridlineShow` | Boolean | Show/hide horizontal gridlines |
| `valueAxis` | `labelDisplayUnits` | Number | Display units for axis labels |
| `labels` | `show` | Boolean | Show/hide data labels on bars |
| `labels` | `labelDisplayUnits` | Number | Display units for data labels |
| `labels` | `fontSize` | Number | Data label font size |
| `labels` | `color` | String | Data label color |
| `legend` | `show` | Boolean | Show/hide legend |
| `legend` | `position` | String | Legend position: `'Top'`, `'Bottom'`, `'Left'`, `'Right'` |
| `legend` | `fontSize` | Number | Legend font size |
| `dataPoint` | `fill` | Color | Per-series color (requires `selector`) |

**Example — Column chart with visible axes, data labels off, legend on top:**

```json
"objects": {
  "categoryAxis": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "labelAngle": {
          "expr": { "Literal": { "Value": "0D" } }
        },
        "fontSize": {
          "expr": { "Literal": { "Value": "9D" } }
        }
      }
    }
  ],
  "valueAxis": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "gridlineShow": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "labelDisplayUnits": {
          "expr": { "Literal": { "Value": "0D" } }
        }
      }
    }
  ],
  "labels": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "false" } }
        }
      }
    }
  ],
  "legend": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "position": {
          "expr": { "Literal": { "Value": "'Top'" } }
        },
        "fontSize": {
          "expr": { "Literal": { "Value": "9D" } }
        }
      }
    }
  ]
}
```

**Per-series color using selector pattern:**

```json
"dataPoint": [
  {
    "properties": {
      "fill": {
        "solid": {
          "color": {
            "expr": { "Literal": { "Value": "'#19F5E2'" } }
          }
        }
      }
    },
    "selector": {
      "metadata": "fact_sales.Total Revenue (GMV)"
    }
  }
]
```

---

### lineChart

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `categoryAxis` | `show` | Boolean | Show/hide category axis |
| `categoryAxis` | `labelAngle` | Number | Axis label rotation in degrees |
| `categoryAxis` | `fontSize` | Number | Axis label font size |
| `valueAxis` | `show` | Boolean | Show/hide value axis |
| `valueAxis` | `gridlineShow` | Boolean | Show/hide horizontal gridlines |
| `valueAxis` | `labelDisplayUnits` | Number | Display units for axis labels |
| `lineStyles` | `showMarker` | Boolean | Show data point markers on lines |
| `lineStyles` | `strokeWidth` | Number | Line thickness in pixels |
| `lineStyles` | `markerShape` | String | Marker shape: `'circle'`, `'square'`, `'diamond'`, `'triangle'`, `'cross'`, `'pentagon'`, `'hexagon'` |
| `labels` | `show` | Boolean | Show/hide data labels |
| `labels` | `labelDisplayUnits` | Number | Display units for data labels |
| `labels` | `fontSize` | Number | Data label font size |

**Example — Line chart with markers enabled, stroke width 2px:**

```json
"objects": {
  "lineStyles": [
    {
      "properties": {
        "showMarker": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "strokeWidth": {
          "expr": { "Literal": { "Value": "2D" } }
        },
        "markerShape": {
          "expr": { "Literal": { "Value": "'circle'" } }
        }
      }
    }
  ],
  "categoryAxis": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "fontSize": {
          "expr": { "Literal": { "Value": "9D" } }
        }
      }
    }
  ],
  "valueAxis": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "gridlineShow": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "labelDisplayUnits": {
          "expr": { "Literal": { "Value": "0D" } }
        }
      }
    }
  ],
  "labels": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "false" } }
        }
      }
    }
  ]
}
```

---

### slicer

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `data` | `mode` | String | Slicer mode: `'Dropdown'`, `'List'`, `'Between'` |
| `data` | `canSelectAll` | Boolean | Show "Select All" option |
| `general` | `orientation` | String | Layout orientation: `'Vertical'`, `'Horizontal'` |
| `selection` | `singleSelect` | Boolean | Restrict to single selection |

**Example — Dropdown slicer with single select:**

```json
"objects": {
  "data": [
    {
      "properties": {
        "mode": {
          "expr": { "Literal": { "Value": "'Dropdown'" } }
        },
        "canSelectAll": {
          "expr": { "Literal": { "Value": "true" } }
        }
      }
    }
  ],
  "general": [
    {
      "properties": {
        "orientation": {
          "expr": { "Literal": { "Value": "'Vertical'" } }
        }
      }
    }
  ],
  "selection": [
    {
      "properties": {
        "singleSelect": {
          "expr": { "Literal": { "Value": "true" } }
        }
      }
    }
  ]
}
```

**Example — Date range slicer (Between mode):**

```json
"objects": {
  "data": [
    {
      "properties": {
        "mode": {
          "expr": { "Literal": { "Value": "'Between'" } }
        }
      }
    }
  ]
}
```

---

### tableEx

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `values` | `fontSize` | Number | Cell font size |
| `values` | `fontFamily` | String | Cell font family (e.g., `'Segoe UI'`) |
| `columnHeaders` | `fontSize` | Number | Header font size |
| `columnHeaders` | `fontFamily` | String | Header font family |
| `columnHeaders` | `bold` | Boolean | Bold header text |
| `grid` | `gridVertical` | Boolean | Show vertical grid lines |
| `grid` | `gridHorizontal` | Boolean | Show horizontal grid lines |
| `grid` | `rowPadding` | Number | Vertical padding per row in pixels |

**Example — Table with grid lines and custom font sizing:**

```json
"objects": {
  "values": [
    {
      "properties": {
        "fontSize": {
          "expr": { "Literal": { "Value": "10D" } }
        },
        "fontFamily": {
          "expr": { "Literal": { "Value": "'Segoe UI'" } }
        }
      }
    }
  ],
  "columnHeaders": [
    {
      "properties": {
        "fontSize": {
          "expr": { "Literal": { "Value": "11D" } }
        },
        "fontFamily": {
          "expr": { "Literal": { "Value": "'Segoe UI'" } }
        },
        "bold": {
          "expr": { "Literal": { "Value": "true" } }
        }
      }
    }
  ],
  "grid": [
    {
      "properties": {
        "gridVertical": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "gridHorizontal": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "rowPadding": {
          "expr": { "Literal": { "Value": "4D" } }
        }
      }
    }
  ]
}
```

---

### visualContainerObjects (All Visual Types)

The `visualContainerObjects` property is set at the same level as `visual.objects` but controls the visual container chrome (title bar, background, border, header). These apply to every visual type.

| Property Group | Sub-Property | Type | Description |
|---|---|---|---|
| `title` | `show` | Boolean | Show/hide visual title |
| `title` | `text` | String | Title text content |
| `title` | `fontSize` | Number | Title font size |
| `title` | `fontColor` | String | Title text color (hex) |
| `title` | `alignment` | String | Title alignment: `'Left'`, `'Center'`, `'Right'` |
| `background` | `show` | Boolean | Show/hide background fill |
| `background` | `color` | String | Background color (hex) |
| `background` | `transparency` | Number | Background transparency (0–100) |
| `border` | `show` | Boolean | Show/hide border |
| `border` | `color` | String | Border color (hex) |
| `border` | `radius` | Number | Border corner radius in pixels |
| `visualHeader` | `show` | Boolean | Show/hide visual header icons |

**Example — Visual with title, background, and border:**

```json
"visualContainerObjects": {
  "title": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "text": {
          "expr": { "Literal": { "Value": "'Total Revenue'" } }
        },
        "fontSize": {
          "expr": { "Literal": { "Value": "12D" } }
        },
        "fontColor": {
          "expr": { "Literal": { "Value": "'#333333'" } }
        },
        "alignment": {
          "expr": { "Literal": { "Value": "'Left'" } }
        }
      }
    }
  ],
  "background": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "color": {
          "expr": { "Literal": { "Value": "'#FFFFFF'" } }
        },
        "transparency": {
          "expr": { "Literal": { "Value": "0D" } }
        }
      }
    }
  ],
  "border": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "true" } }
        },
        "color": {
          "expr": { "Literal": { "Value": "'#E0E0E0'" } }
        },
        "radius": {
          "expr": { "Literal": { "Value": "4D" } }
        }
      }
    }
  ],
  "visualHeader": [
    {
      "properties": {
        "show": {
          "expr": { "Literal": { "Value": "false" } }
        }
      }
    }
  ]
}
```

---

### filterConfig

The `filterConfig` property defines per-visual filters. It sits at the same level as `visual` inside the visual container. Each filter entry requires a unique `name` (20-character hex string), a `field` reference, and a `type`.

**Filter types:**

| Type | Use Case |
|---|---|
| `Categorical` | Filters on column values (dimension fields) |
| `Advanced` | Filters on measure values (numeric comparisons) |
| `Advanced` (date range) | Filters on date columns using `And` + `DateSpan` for date range (`>=` start, `<=` end) |
| `RelativeDate` | Filters on date columns using `Now` / `DateAdd` expressions for rolling current-date windows |

**Example — Categorical filter on a column:**

```json
"filterConfig": {
  "filters": [
    {
      "name": "a1b2c3d4e5f678901234",
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "dim_date" } },
          "Property": "year"
        }
      },
      "type": "Categorical"
    }
  ]
}
```

**Example — Advanced filter on a measure:**

```json
"filterConfig": {
  "filters": [
    {
      "name": "b2c3d4e5f6789012345a",
      "field": {
        "Measure": {
          "Expression": { "SourceRef": { "Entity": "fact_sales" } },
          "Property": "Total Revenue (GMV)"
        }
      },
      "type": "Advanced"
    }
  ]
}
```

**Example — Combined filters (typical for charts):**

```json
"filterConfig": {
  "filters": [
    {
      "name": "a1b2c3d4e5f678901234",
      "field": {
        "Column": {
          "Expression": { "SourceRef": { "Entity": "dim_date" } },
          "Property": "year"
        }
      },
      "type": "Categorical"
    },
    {
      "name": "c3d4e5f67890123456ab",
      "field": {
        "Measure": {
          "Expression": { "SourceRef": { "Entity": "fact_sales" } },
          "Property": "Total Revenue (GMV)"
        }
      },
      "type": "Advanced"
    }
  ]
}
```

**Example — Advanced date range filter (And + DateSpan):**

When a SQL query contains an **absolute** date-level filter (e.g., `FROM '2017-01-01' TO '2017-12-31'`), use an `Advanced` filter with an `And` condition combining two `Comparison` nodes — one for `>=` (start date) and one for `<=` (end date). Each comparison wraps the date literal in a `DateSpan` with `TimeUnit: 5` (day granularity).

**`ComparisonKind` values:**

| Value | Logical Meaning | Description |
|---|---|---|
| `0` | Equal | The values are identical. |
| `1` | Greater Than | The first value is strictly larger than the second. |
| `2` | Greater Than or Equal | The first value is larger than or equal to the second. |
| `3` | Less Than | The first value is strictly smaller than the second. |
| `4` | Less Than or Equal | The first value is smaller than or equal to the second. |
| `5` | Not Equal | The values are different. |

**`TimeUnit` values:**

| Value | TimeUnit | Description |
|---|---|---|
| `0` | None | No specific time unit specified. |
| `1` | Year | Annual level granularity. |
| `2` | Quarter | Three-month period. |
| `3` | Month | Standard calendar month. |
| `4` | Week | 7-day period. |
| `5` | Day | 24-hour period. |
| `6` | Hour | Hourly granularity. |
| `7` | Minute | Minute-level granularity. |

**Placeholders for absolute date ranges:**

- `{{DateRangeFilterGuid}}` — unique 20-character hex GUID for this filter
- `{{DateRangeEntity}}` — the date table name (e.g., `dim_date`)
- `{{DateRangeProperty}}` — the date column name (e.g., `date`)
- `{{DateRangeAlias}}` — the source alias for the date table in the `From` clause
- `{{DateStart}}` — the start date literal (e.g., `"datetime'2017-01-01T00:00:00'"`)
- `{{DateEnd}}` — the end date literal (e.g., `"datetime'2017-12-31T00:00:00'"`)

```json
{
  "name": "{{DateRangeFilterGuid}}",
  "field": {
    "Column": {
      "Expression": {
        "SourceRef": {
          "Entity": "{{DateRangeEntity}}"
        }
      },
      "Property": "{{DateRangeProperty}}"
    }
  },
  "type": "Advanced",
  "filter": {
    "Version": 2,
    "From": [
      {
        "Name": "{{DateRangeAlias}}",
        "Entity": "{{DateRangeEntity}}",
        "Type": 0
      }
    ],
    "Where": [
      {
        "Condition": {
          "And": {
            "Left": {
              "Comparison": {
                "ComparisonKind": 2,
                "Left": {
                  "Column": {
                    "Expression": {
                      "SourceRef": {
                        "Source": "{{DateRangeAlias}}"
                      }
                    },
                    "Property": "{{DateRangeProperty}}"
                  }
                },
                "Right": {
                  "DateSpan": {
                    "Expression": {
                      "Literal": {
                        "Value": "{{DateStart}}"
                      }
                    },
                    "TimeUnit": 5
                  }
                }
              }
            },
            "Right": {
              "Comparison": {
                "ComparisonKind": 4,
                "Left": {
                  "Column": {
                    "Expression": {
                      "SourceRef": {
                        "Source": "{{DateRangeAlias}}"
                      }
                    },
                    "Property": "{{DateRangeProperty}}"
                  }
                },
                "Right": {
                  "DateSpan": {
                    "Expression": {
                      "Literal": {
                        "Value": "{{DateEnd}}"
                      }
                    },
                    "TimeUnit": 5
                  }
                }
              }
            }
          }
        }
      }
    ]
  }
}
```

The `And` condition goes inside `Where[0].Condition` — it is not a second item in the `Where` array. Do **not** include `"howCreated": "User"` in any filter entry.

**Current-date-relative ranges (e.g., "last 12 months", "last 90 days"):**

When the Genie query or user intent includes a rolling period relative to **today**, emit a native PBIR `RelativeDate` filter instead of substituting precomputed literal start/end dates.

**Placeholders for native `RelativeDate`:**

- `{{RelativeDateFilterGuid}}` — unique 20-character hex GUID for this filter
- `{{RelativeDateEntity}}` — the date table name (e.g., `dim_date` or `dim_date_delivery`)
- `{{RelativeDateProperty}}` — the date column name (typically `date`)
- `{{RelativeDateAlias}}` — the source alias for the date table in the `From` clause
- `{{RelativeDateAmount}}` — rolling period size (e.g., `12`)
- `{{RelativeDateTimeUnit}}` — PBIR `DateAdd` time unit for the requested period

```json
{
  "name": "{{RelativeDateFilterGuid}}",
  "field": {
    "Column": {
      "Expression": {
        "SourceRef": {
          "Entity": "{{RelativeDateEntity}}"
        }
      },
      "Property": "{{RelativeDateProperty}}"
    }
  },
  "type": "RelativeDate",
  "filter": {
    "Version": 2,
    "From": [
      {
        "Name": "{{RelativeDateAlias}}",
        "Entity": "{{RelativeDateEntity}}",
        "Type": 0
      }
    ],
    "Where": [
      {
        "Condition": {
          "Between": {
            "Expression": {
              "Column": {
                "Expression": {
                  "SourceRef": {
                    "Source": "{{RelativeDateAlias}}"
                  }
                },
                "Property": "{{RelativeDateProperty}}"
              }
            },
            "LowerBound": {
              "DateSpan": {
                "Expression": {
                  "DateAdd": {
                    "Expression": {
                      "DateAdd": {
                        "Expression": {
                          "Now": {}
                        },
                        "Amount": 1,
                        "TimeUnit": 0
                      }
                    },
                    "Amount": -{{RelativeDateAmount}},
                    "TimeUnit": {{RelativeDateTimeUnit}}
                  }
                },
                "TimeUnit": 0
              }
            },
            "UpperBound": {
              "DateSpan": {
                "Expression": {
                  "Now": {}
                },
                "TimeUnit": 0
              }
            }
          }
        }
      }
    ]
  }
}
```

Use the reference pattern from `generated-reports/DeliveryDaysTrends/.../visual.json` as the baseline for month windows. Treat `"howCreated": "User"` as a Desktop-authored artifact, not a required generated property.

Choose the relative-date table to match the requested timeline:

- Purchase/order timeline -> `dim_date.date`
- Delivery timeline -> `dim_date_delivery.date`

**Data-anchored rolling ranges (e.g., "latest 12 months in the data"):**

Do **not** emit native `RelativeDate` for data-anchored windows. Native `RelativeDate` always anchors to `Now`, not to the max available row in the model.

Instead:

1. Ask Stage 1 to materialize a helper measure or flag such as `Show Last 12 Purchase Months` or `Show Last 12 Delivery Months`.
2. Reuse the standard `Advanced` measure-filter pattern to require that helper field to evaluate to `1` for the visual.
3. Keep the axis/filter date role aligned with the helper measure's anchor table (`dim_date`, `dim_date_delivery`, etc.).

This preserves deterministic historical-window behavior for sparse datasets.

**Relative date ranges (legacy literal date substitution pattern):**

Only use literal `{{DateStart}}` / `{{DateEnd}}` substitution when the request is for an explicit absolute range or when a downstream consumer cannot accept `RelativeDate`.

| User Intent | `{{DateStart}}` | `{{DateEnd}` |
|---|---|---|
| Last 90 days | `datetime'<currentDate - 90 days>T00:00:00'` | `datetime'<currentDate>T00:00:00'` |
| Last 30 days | `datetime'<currentDate - 30 days>T00:00:00'` | `datetime'<currentDate>T00:00:00'` |
| Last 6 months | `datetime'<currentDate - 6 months>T00:00:00'` | `datetime'<currentDate>T00:00:00'` |
| Last year | `datetime'<currentDate - 365 days>T00:00:00'` | `datetime'<currentDate>T00:00:00'` |
| Year-to-date | `datetime'<Jan 1 of current year>T00:00:00'` | `datetime'<currentDate>T00:00:00'` |

**How to compute:**

1. Determine the current date at generation time (e.g., `2026-02-26`).
2. Subtract the specified duration to get the start date.
3. Format both dates as `datetime'YYYY-MM-DDT00:00:00'` (Power BI datetime literal format).

**Example — "last 90 days" generated on 2026-02-26:**

- `{{DateStart}}` = `datetime'2025-11-28T00:00:00'`
- `{{DateEnd}}` = `datetime'2026-02-26T00:00:00'`

These computed values are substituted directly into the `DateSpan` → `Literal` → `Value` fields in the absolute date-range filter. The `{{DateRangeEntity}}` and `{{DateRangeProperty}}` should reference the date table and date column from the semantic model (e.g., `dim_date.date`).

---

### References

- [Microsoft PBIR VisualContainer Schema](https://github.com/microsoft/json-schemas/tree/main/fabric/item/report/definition/visualContainer) — Official JSON schema definitions (schema 2.5.0 current as of January 2026)
- [Power BI Desktop Project Report Documentation](https://learn.microsoft.com/en-us/power-bi/developer/projects/projects-report) — Microsoft documentation for PBIR report format
- [Community pbir-visuals Templates](https://github.com/cn-dataworks/pbir-visuals) — Open-source PBIR visual templates with placeholder patterns

## Preserving SemanticModel Content

**Critical:** After the SemanticModel is copied from the existing project (Stage 4), do **NOT** remove any tables, models, relationships, or definition files from the SemanticModel — even if they are not directly referenced by the current visual. The complete SemanticModel must remain intact because:

- Other visuals or reports may depend on those tables/relationships
- Removing tables breaks `ref table` declarations in `model.tmdl`
- Removing relationships breaks foreign key integrity
- Power BI Desktop validates the entire model on load, not just the visual's bindings

The visual generator should only **add** report files (visual.json, page.json, etc.) — never delete or modify existing SemanticModel content.

## Error Handling

| Situation | Resolution |
|---|---|
| Template placeholder not found in mapping | Use empty string; log warning |
| Unknown visual type | Fall back to `tableEx` template |
| Missing table/measure name | Use placeholder with TODO comment |
| Page dimensions exceed 1280x720 | Clip to default dimensions |
