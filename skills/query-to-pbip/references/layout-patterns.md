# Layout Patterns Reference

Page layout grid patterns for positioning visuals within Power BI report pages. Use this document when executing the visual-generator sub-skill (Stage 3) to determine visual placement.

## Page Dimensions

Default Power BI page dimensions:
- Width: 1280 pixels
- Height: 720 pixels
- Display mode: `FitToPage`

## Single Visual Layouts

### Full Page (Single Visual)

Position the visual to fill the page with standard margins:

```json
{
  "x": 20,
  "y": 20,
  "z": 0,
  "width": 1240,
  "height": 680
}
```

### Centered Card

For a single card KPI, center it on the page:

```json
{
  "x": 440,
  "y": 260,
  "z": 0,
  "width": 400,
  "height": 200
}
```

## Multi-Visual Layouts

### Two-Column Layout

Side-by-side visuals with equal width:

| Position | x | y | width | height |
|---|---|---|---|---|
| Left | 20 | 20 | 610 | 680 |
| Right | 650 | 20 | 610 | 680 |

### Header + Detail

KPI card row on top, detail visual below:

| Position | x | y | width | height |
|---|---|---|---|---|
| Card 1 | 20 | 20 | 300 | 150 |
| Card 2 | 340 | 20 | 300 | 150 |
| Card 3 | 660 | 20 | 300 | 150 |
| Card 4 | 980 | 20 | 280 | 150 |
| Detail | 20 | 190 | 1240 | 510 |

### 2x2 Grid

Four equal quadrants:

| Position | x | y | width | height |
|---|---|---|---|---|
| Top-Left | 20 | 20 | 610 | 330 |
| Top-Right | 650 | 20 | 610 | 330 |
| Bottom-Left | 20 | 370 | 610 | 330 |
| Bottom-Right | 650 | 370 | 610 | 330 |

### Dashboard with Slicer

Slicer panel on left, main visual on right:

| Position | x | y | width | height |
|---|---|---|---|---|
| Slicer | 20 | 20 | 250 | 680 |
| Main Visual | 290 | 20 | 970 | 680 |

## Visual Container Structure

Every visual must be wrapped in a visual container with positioning:

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/1.0.0/schema.json",
  "name": "<unique-visual-name>",
  "position": {
    "x": <x>,
    "y": <y>,
    "z": <z>,
    "width": <width>,
    "height": <height>,
    "tabOrder": <tabOrder>
  },
  "visual": {
    "visualType": "<type>",
    "query": { ... },
    "objects": { ... }
  }
}
```

## Page Container Structure

```json
{
  "$schema": "https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/1.0.0/schema.json",
  "name": "<page-guid>",
  "displayName": "<Page Title>",
  "displayOption": 1,
  "height": 720,
  "width": 1280,
  "visualContainers": [
    { ... }
  ]
}
```

## Z-Order Rules

- Background visuals: z = 0
- Data visuals: z = 1000+ (increment by 1000)
- Slicer overlays: z = 10000+
- Title/header text: z = 20000+

## Tab Order

Set `tabOrder` sequentially starting from 0 for accessibility:
- First visual: `tabOrder: 0`
- Second visual: `tabOrder: 1000`
- Third visual: `tabOrder: 2000`

This ensures keyboard navigation follows visual reading order (left-to-right, top-to-bottom).
