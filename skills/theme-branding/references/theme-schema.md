# Power BI Theme JSON — Canonical Reference

Authoritative reference for the Power BI report-theme JSON format used by the toolkit. Aligned with Microsoft's official documentation:

- [Use report themes in Power BI](https://learn.microsoft.com/power-bi/create-reports/desktop-report-themes)
- [Create custom report themes in Power BI Desktop](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom)

## Top-Level Structure

A full theme file has up to six top-level groups. Only `name` is strictly required; everything else is optional and inherits from Power BI defaults when omitted.

```json
{
  "$schema": "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.140.json",
  "name": "MyTheme",
  "dataColors":   ["#hex", "..."],
  "good": "#hex", "neutral": "#hex", "bad": "#hex",
  "maximum": "#hex", "center": "#hex", "minimum": "#hex", "null": "#hex",
  "background": "#hex", "secondaryBackground": "#hex",
  "foreground": "#hex", "secondaryForeground": "#hex",
  "tableAccent": "#hex",
  "textClasses": { /* see below */ },
  "visualStyles": { /* see below */ }
}
```

Referencing the `$schema` URL in your JSON enables editor IntelliSense and validation (VS Code, JSON Schema Store).

## 1. Theme Colors

Colors used by visuals to render series, sentiment, and gradient scales. From [Set theme colors](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#set-theme-colors).

| Slot | Required | Purpose |
|---|---|---|
| `dataColors` | yes | Array of hex strings used by visuals for **dynamic series** (categories, columns, slices). Provide at least 8 entries — the report rotates through them in order. |
| `good`, `neutral`, `bad` | no | Sentiment colors for KPI visuals, conditional formatting, and waterfall increase/decrease/total. |
| `maximum`, `center`, `minimum`, `null` | no | Endpoints for **diverging color scales** (e.g., conditional formatting gradients on tables and matrices). |

### Dynamic vs. static series

From *Use report themes → Colors used by dynamic and static series*:

- **Dynamic series** (categorical breakdown) — colors are auto-assigned in order from `dataColors`. A new theme **does** recolor these.
- **Static series** (a fixed measure like "Total Sales") — once a user explicitly picks a color in the format pane, it is locked. A new theme **does NOT** override an explicit color choice.

Design implication: keep `dataColors[0..7]` legible against both `background` and `secondaryBackground`.

## 2. Structural Colors

From [Set structural colors](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#set-structural-colors). These are the **named** structural slots Power BI applies across non-visual chrome (page background, axis lines, gridlines, table accents).

| Slot | Used For |
|---|---|
| `background` | Default page and visual background |
| `secondaryBackground` | Alternate background (e.g., gridlines, axis backplate, table banded rows) |
| `foreground` | Default text/label color |
| `secondaryForeground` | Subdued text (axis labels, footnotes, secondary labels) |
| `tableAccent` | Accent line / header underline in table & matrix visuals |

Power BI also reads three derived neutrals (`foregroundNeutralSecondary`, `backgroundNeutral`, `tableAccent`) from these primary structural slots when not explicitly provided.

## 3. Formatted Text Defaults (`textClasses`)

From [Set formatted text defaults](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#set-formatted-text-defaults). Twelve named **text classes** drive default typography for visuals. Each class accepts `fontFace`, `fontSize` (point size), and `color`.

| Class | Default Used For |
|---|---|
| `callout` | KPI / card big-number value |
| `title` | Visual titles |
| `header` | Slicer headers, key influencers headers |
| `label` | Generic visual labels |
| `largeLabel` | Map data labels, R/Python visual labels |
| `smallLabel` | Reference line labels, slicer date labels |
| `semiboldLabel` | Key influencers profiled |
| `boldLabel` | Matrix grand totals |
| `largeLightLabel` | Card category labels |
| `lightLabel` | Most data and axis labels, legend text |
| `circularGauge` | Gauge target & callout |
| `colorLink` | Hyperlink text in tables |

```json
"textClasses": {
  "callout":         { "fontFace": "Segoe UI Light", "fontSize": 36, "color": "#1F3864" },
  "title":           { "fontFace": "Segoe UI",        "fontSize": 14, "color": "#1F3864" },
  "header":          { "fontFace": "Segoe UI Semibold","fontSize": 12, "color": "#333333" },
  "label":           { "fontFace": "Segoe UI",        "fontSize": 10, "color": "#333333" },
  "lightLabel":      { "fontFace": "Segoe UI",        "fontSize": 9,  "color": "#666666" },
  "largeLabel":      { "fontFace": "Segoe UI",        "fontSize": 12, "color": "#333333" },
  "smallLabel":      { "fontFace": "Segoe UI",        "fontSize": 8,  "color": "#666666" },
  "semiboldLabel":   { "fontFace": "Segoe UI Semibold","fontSize": 10, "color": "#333333" },
  "boldLabel":       { "fontFace": "Segoe UI Bold",   "fontSize": 10, "color": "#333333" },
  "largeLightLabel": { "fontFace": "Segoe UI",        "fontSize": 11, "color": "#666666" }
}
```

Font sizes are in **points**, not pixels. Keep them between 6 and 72.

## 4. Visual Property Defaults (`visualStyles`)

From [Set properties for visual types](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#set-properties-for-visual-types). Three-level keyed object:

```text
visualStyles.<visualType>.<styleName>.<cardName>
```

- `<visualType>` — `*` (all visuals) or a specific visual name (`columnChart`, `lineChart`, `cardVisual`, `tableEx`, `pivotTable`, `slicer`, `filledMap`, `pieChart`, `donutChart`, `scatterChart`, `lineClusteredColumnComboChart`, `clusteredBarChart`, `kpi`, etc.)
- `<styleName>` — `*` (default style) or a named **style preset** (see §5)
- `<cardName>` — name of the formatting card (`background`, `border`, `title`, `labels`, `categoryLabels`, `legend`, `dataPoint`, `valueAxis`, `categoryAxis`, `general`, etc.)

Each card maps to an array of property objects. Most cards take a single-element array.

```json
"visualStyles": {
  "*": {
    "*": {
      "background":    [{ "show": true,  "color": { "solid": { "color": "#FFFFFF" } }, "transparency": 0 }],
      "border":        [{ "show": false }],
      "title":         [{ "show": true,  "fontColor": { "solid": { "color": "#1F3864" } }, "fontSize": 14 }],
      "visualHeader":  [{ "show": false }]
    }
  },
  "cardVisual": {
    "*": {
      "labels":         [{ "fontSize": 28, "color": { "solid": { "color": "#1F3864" } } }],
      "categoryLabels": [{ "fontSize": 11, "color": { "solid": { "color": "#666666" } } }]
    }
  },
  "page": {
    "*": {
      "background": [{ "color": { "solid": { "color": "#FFFFFF" } }, "transparency": 0 }],
      "outspace":   [{ "color": { "solid": { "color": "#F7F7F7" } }, "transparency": 0 }]
    }
  }
}
```

### Finding the right card and property names

Three options (from [Find visual properties](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#find-visual-properties)):

1. **JSON Schema** — use the `$schema` URL above; your editor will autocomplete valid `<visualType>` and `<cardName>` values.
2. **Formatting pane in Power BI Desktop** — names in the on-screen format pane usually correspond 1:1 to `cardName`. Property labels in the pane match property keys after camelCasing (e.g., "Font size" → `fontSize`).
3. **PBIR files** — open `<Project>.Report/definition/pages/<page>/visuals/<visual>/visual.json` and inspect the `objects` section. The keys you see (`background`, `title`, `labels`, …) are exactly the `cardName` values you place in `visualStyles`.

## 5. Style Presets

From [Create style presets in custom themes](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#create-style-presets-in-custom-themes). Style presets let one theme ship multiple named variants of the same visual (e.g., a "Hero" card style and a "Mini" card style). Users pick presets from the format pane.

### Defining a preset

```json
"visualStyles": {
  "cardVisual": {
    "*":    { /* default; applies when no preset is selected */ },
    "Hero": {
      "labels":         [{ "fontSize": 48 }],
      "categoryLabels": [{ "fontSize": 14 }],
      "background":     [{ "color": { "solid": { "color": "#1F3864" } } }]
    },
    "Mini": {
      "labels":         [{ "fontSize": 18 }],
      "categoryLabels": [{ "fontSize": 9 }]
    }
  }
}
```

Apply via the format pane → *General → Style preset* dropdown.

## 6. Color & Fill Value Syntax

Themes use a consistent wrapped-color syntax everywhere except `dataColors` and structural slots:

| Where | Syntax |
|---|---|
| `dataColors[i]`, structural slots, `good`/`bad`, etc. | Bare hex string: `"#1F3864"` |
| Inside `textClasses[].color` | Bare hex string |
| Inside `visualStyles` cards | Wrapped object: `{ "solid": { "color": "#1F3864" } }` |

For colors that should pull from the **theme palette** rather than be hard-coded, reference by index inside `visualStyles`:

```json
"color": { "solid": { "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": 0 } } } } }
```

`ColorId` is the zero-based index into `dataColors`. `Percent` is a tint/shade percentage (positive = lighter, negative = darker, 0 = exact).

## 7. Tips for Authoring (from MS docs)

From [Tips for setting values in the JSON theme file](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#tips-for-setting-values-in-the-json-theme-file):

1. **Use `*` to set defaults**, then override for specific visual types — saves duplication.
2. **Property names are case-sensitive** (`fontSize` works, `fontsize` does not).
3. **Always wrap color values inside `visualStyles`** as `{ "solid": { "color": "#hex" } }`.
4. **Test incrementally** — apply, observe, adjust. The format pane reveals what's themable.
5. **Save the in-pane theme** as a starting point: *View → Themes → Customize → Save Current Theme*.
6. **Include the `$schema`** declaration for editor support.
7. **Provide ≥ 8 `dataColors`** — fewer entries cause Power BI to fall back to the default palette.

## 8. Built-in Themes (for reference)

Power BI Desktop ships these built-in themes. A custom theme should look intentional next to them:

- Default (Power BI light)
- Power BI (dark variant)
- Sunset
- Twilight
- Solar
- High contrast
- Innovate, Bloom, Tidal, Temperature, Storm, Autumn, Classic, City Park, Frontier, Highrise

Users apply built-ins from *View → Themes*. Custom themes coexist; the most recent **Browse for themes / Import theme** wins.

## 9. Considerations & Limitations (from MS docs)

- Some visual properties are **not themable** (most notably properties that are part of a visual's data binding such as field names, conditional-formatting rules tied to specific values, and a small set of legacy visuals).
- Custom visuals from AppSource may ignore themes or honor only a subset.
- Themes affect new visuals **and** existing visuals that haven't had explicit overrides. Once a user manually sets a property, that property is locked against the theme.
- Power BI service applies themes the same way Desktop does for PBIP/PBIX models — no service-side patching needed.
- Theme JSON has no formal version field; the `$schema` URL implicitly versions the file by date.

## 10. Validation Rules (enforced by `apply_theme.py`)

1. File parses as valid JSON.
2. `name` is present and non-empty.
3. `dataColors` is an array of **≥ 8** hex strings (each `^#[0-9A-Fa-f]{6}$`).
4. All hex strings in theme colors (`good`/`neutral`/`bad`/`maximum`/`center`/`minimum`/`null`) and structural colors (`background`/`secondaryBackground`/`foreground`/`secondaryForeground`/`tableAccent`) are valid 6-digit hex.
5. `textClasses[*].fontSize` (if present) is an integer between 6 and 72.
6. `textClasses[*].color` (if present) is a valid hex string.
7. `visualStyles` (if present) is a nested object — not validated for card/property correctness; rely on the official `$schema` for that.
8. Theme file basename matches the `name` value (case-insensitive) — `Corporate.json` ↔ `"name": "Corporate"`.

## 11. Programmatic Extract & Apply

From [Extract and apply themes programmatically](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#extract-and-apply-themes-programmatically):

- **Extract** from a `.pbix`: rename to `.zip`, extract `Report/StaticResources/SharedResources/BaseThemes/<name>.json`.
- **Extract** from a `.pbip`: read directly from `<Project>.Report/StaticResources/SharedResources/BaseThemes/<name>.json` — no zip step required (this is the path `theme-branding/scripts/apply_theme.py` writes to).
- **Apply** programmatically: write the JSON into the BaseThemes folder and update `<Project>.Report/definition/report.json` `themeCollection.baseTheme.name` + `resourcePackages[].items[]` entry. The `apply_theme.py` script does exactly this.
