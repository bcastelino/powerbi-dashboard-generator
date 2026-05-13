---
name: theme-branding
description: Applies professional themes and corporate branding to a generated PBIP project. This skill should be used after the report files are written and before the final dashboard is delivered, to swap in a chosen theme JSON, register it in report.json, and optionally inject a logo and corporate color palette. Provides four built-in presets (corporate, modern, minimal, dark) and supports custom theme files.
---

# Theme & Branding

Apply a professional theme to a generated PBIP project. This skill swaps the default `CY25SU11` theme for a chosen theme (preset or custom), updates `report.json` to reference it, and optionally applies logo / corporate color palette overrides.

This skill follows Microsoft's official report-theme techniques:

- [Use report themes in Power BI](https://learn.microsoft.com/power-bi/create-reports/desktop-report-themes)
- [Create custom report themes in Power BI Desktop](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom)

See `references/theme-schema.md` for the full canonical reference.

## When to Use This Skill

- After `query-to-pbip` has produced a PBIP and before `bi-dash-creator` composes the dashboard
- The user requests a specific look ("corporate", "modern", "minimal", "dark", or a brand)
- A custom theme JSON file is supplied
- A logo or color palette needs to be embedded

## Inputs

- **PBIP project path** — `<ProjectName>/` directory produced by `query-to-pbip`
- **Theme selector** — One of: `corporate | modern | minimal | dark | custom`
- **Custom theme path** (optional) — Required when `theme = custom`; path to a Power BI theme JSON file
- **Logo path** (optional) — PNG/SVG file to embed as a top-of-page image
- **Color overrides** (optional) — `{ primary: "#hex", secondary: "#hex", accent: "#hex" }`

## Built-in Theme Presets

| Preset | Style | Primary | Secondary | Background | Foreground |
|---|---|---|---|---|---|
| `corporate` | Professional, conservative, navy/grey | `#1F3864` | `#5B9BD5` | `#FFFFFF` | `#333333` |
| `modern` | Bold, high-contrast, teal/coral | `#19A0AA` | `#F15A29` | `#F7F7F7` | `#222222` |
| `minimal` | Monochrome, lots of whitespace | `#444444` | `#888888` | `#FFFFFF` | `#111111` |
| `dark` | Dark mode, neon accents | `#19F5E2` | `#FF6F61` | `#1E1E1E` | `#EEEEEE` |

Preset theme JSONs live in `assets/themes/`. Each preset declares the `$schema` URL, a full 8-color `dataColors` palette, all five structural colors (`background`, `secondaryBackground`, `foreground`, `secondaryForeground`, `tableAccent`), the four sentiment/diverging slots, the ten core `textClasses`, and baseline `visualStyles` for `*`, `page`, and `cardVisual`.

## Theme Anatomy (the four authoring surfaces)

A Power BI theme has four layered surfaces. Author each in order; later surfaces override earlier ones.

### 1. Theme colors — the data palette

- `dataColors[]` — the rotating palette for **dynamic series**. Provide ≥ 8 entries.
- `good` / `neutral` / `bad` — KPI sentiment + waterfall increase/decrease/total + conditional formatting sentiment.
- `maximum` / `center` / `minimum` / `null` — endpoints for diverging color scales (gradient conditional formatting on tables/matrices).

**Dynamic vs. static series:** dynamic series (one color per category) are auto-themed. Static series whose color was explicitly picked in the format pane are locked and **not** overridden by a theme swap. Account for this when planning visual brand consistency.

### 2. Structural colors — the chrome palette

Five named slots drive non-data colors across page, gridlines, axes, and tables:

- `background`, `secondaryBackground`
- `foreground`, `secondaryForeground`
- `tableAccent`

### 3. `textClasses` — typography defaults

Ten text classes cover every label in a Power BI visual: `callout`, `title`, `header`, `label`, `largeLabel`, `smallLabel`, `semiboldLabel`, `boldLabel`, `largeLightLabel`, `lightLabel`. Each takes `fontFace`, `fontSize` (points, 6–72), and `color`.

### 4. `visualStyles` — per-card overrides

Three-level keyed object: `visualStyles.<visualType>.<styleName>.<cardName>`.

- `<visualType>` — `*` (default) or a specific name (`columnChart`, `lineChart`, `cardVisual`, `tableEx`, `pivotTable`, `slicer`, `page`, etc.).
- `<styleName>` — `*` (default style) or a named **style preset** (see below).
- `<cardName>` — formatting card (`background`, `border`, `title`, `labels`, `legend`, `dataPoint`, `valueAxis`, `categoryAxis`, `outspace`, etc.).

Colors **inside** `visualStyles` must be wrapped as `{ "solid": { "color": "#hex" } }` — unlike the bare hex strings in theme/structural colors.

### Binding to the palette via `ThemeDataColor`

Inside `visualStyles`, prefer **palette references** over hard-coded hex so the visual recolors automatically if the palette changes:

```json
"color": { "solid": { "color": { "expr": { "ThemeDataColor": { "ColorId": 0, "Percent": 0 } } } } }
```

`ColorId` is the zero-based index into `dataColors`; `Percent` is a tint (positive) or shade (negative).

### Style presets (multiple looks per visual type)

A single theme can ship multiple named looks (e.g., `Hero` vs `Mini` card styles). Users select presets in the format pane. Define them under `visualStyles.<visualType>.<StyleName>`:

```json
"cardVisual": {
  "*":    { /* default */ },
  "Hero": { "labels": [{ "fontSize": 48 }] },
  "Mini": { "labels": [{ "fontSize": 18 }] }
}
```

### `$schema` declaration

Every preset and custom theme should reference the official schema for editor IntelliSense + validation:

```json
"$schema": "https://raw.githubusercontent.com/microsoft/powerbi-desktop-samples/main/Report%20Theme%20JSON%20Schema/reportThemeSchema-2.140.json"
```

## Finding Visual Property Names

From Microsoft's [Find visual properties](https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom#find-visual-properties), use one of:

1. **`$schema` autocomplete** in VS Code / a JSON editor
2. **Format pane** in Power BI Desktop — card names match `cardName`, property labels match property keys after camelCasing
3. **PBIR files** — inspect `<Project>.Report/definition/pages/<page>/visuals/<visual>/visual.json` `objects` section; the keys you see (`background`, `title`, `labels`, …) are exactly the `cardName` values needed in `visualStyles`

## Workflow

### Step 1: Locate the PBIP

Find `<ProjectName>.Report/StaticResources/SharedResources/BaseThemes/` inside the project directory. This is where the active theme JSON lives.

### Step 2: Select the Theme File

- If `theme = corporate | modern | minimal | dark` → copy `assets/themes/<theme>.json` into the BaseThemes directory
- If `theme = custom` → copy the user-supplied theme JSON into the BaseThemes directory (validate it first against `references/theme-schema.md` §10 — Validation Rules)
- If `theme` is omitted or unknown → keep the default `CY25SU11.json`

### Step 3: Apply Color & Branding Overrides (Optional)

When the user supplies brand overrides, patch the theme JSON in this order so all surfaces stay consistent:

1. **`dataColors[0..2]`** — set `primary` / `secondary` / `accent` if provided.
2. **`tableAccent`** — mirror `primary` so tables get the brand accent.
3. **`title` text class color** — use `primary` for visual titles.
4. **`good` / `bad`** — leave defaults unless the user supplies sentiment overrides (the default green/red are accessibility-tuned).
5. **`visualStyles.cardVisual.*.labels[0].color`** — if the card big-number color is hard-coded in the preset, swap to `primary`. Prefer rewriting it as a `ThemeDataColor` expression (`ColorId: 0`) so future palette swaps cascade automatically.

Preserve all other theme properties (including `$schema`, `textClasses`, structural slots not being changed, and existing `visualStyles` cards).

### Step 4: Update `report.json`

In `<ProjectName>.Report/definition/report.json`, update the `themeCollection.baseTheme.name` to match the new theme's `name` property. Update `resourcePackages[].items[]` to point at the new theme file path:

```json
"resourcePackages": [
  {
    "name": "SharedResources",
    "type": "SharedResources",
    "items": [
      {
        "name": "<themeName>",
        "path": "BaseThemes/<themeName>.json",
        "type": "BaseTheme"
      }
    ]
  }
]
```

### Step 5: Embed Logo (Optional)

If a logo path was supplied:

1. Copy the image into `<ProjectName>.Report/StaticResources/RegisteredResources/<sanitized-name>.<ext>`
2. Register it in `report.json` under `resourcePackages[]` with `type: "RegisteredResources"`
3. On page 1, add a new image visual at the top of the page (suggested position: `x: 20, y: 10, w: 200, h: 60`). The image visual references the registered resource by name.

### Step 6: Validate (per Microsoft schema)

After modifications, verify:

1. Theme JSON parses as valid JSON.
2. `name` is present and matches the file basename and the `themeCollection.baseTheme.name` in `report.json`.
3. `dataColors` has ≥ 8 entries; each is a 6-digit hex.
4. All structural color slots (`background`, `secondaryBackground`, `foreground`, `secondaryForeground`, `tableAccent`) and sentiment/diverging slots are valid hex when present.
5. All `textClasses[*].fontSize` values are integers in `[6, 72]`; all `textClasses[*].color` values are valid hex.
6. Colors inside `visualStyles` are wrapped as `{ "solid": { "color": "#hex" } }` (or `ThemeDataColor` expressions) — never bare hex strings.
7. `resourcePackages[].items[].path` files all exist on disk.
8. The default `CY25SU11` theme entry is **not removed** if it's still referenced anywhere.

### Step 7: Re-zip (Optional)

If the project was previously zipped, re-run `query-to-pbip/scripts/package_pbip.py` to refresh the archive.

## Resources

- **`assets/themes/corporate.json`** — Corporate preset theme
- **`assets/themes/modern.json`** — Modern preset theme
- **`assets/themes/minimal.json`** — Minimal preset theme
- **`assets/themes/dark.json`** — Dark preset theme
- **`scripts/apply_theme.py`** — End-to-end theme application script (copy theme, patch report.json, validate)
- **`references/theme-schema.md`** — Power BI theme JSON schema reference and validation rules

## Error Handling

| Error | Resolution |
|---|---|
| Theme JSON fails schema validation | Stop and surface validation errors to the user |
| `report.json` not found | Verify the PBIP path is correct |
| Logo file not found | Skip logo embedding; warn the user |
| Image visual type not supported by the current report version | Fall back to embedding logo via theme `visualStyles` |
| `visualStyles` color is bare hex (not wrapped) | Reject — themes silently ignore bare hex inside `visualStyles`. Wrap as `{ "solid": { "color": "#hex" } }` |
| User reports a visual ignoring the theme | Likely a static series with an explicit color override, or a non-themable property. See `references/theme-schema.md` §9 Considerations & Limitations |

## Considerations & Limitations (from Microsoft docs)

- **Locked properties**: once a user explicitly picks a color or font in the format pane on a static series, the theme no longer overrides it.
- **Non-themable properties**: a small set of properties (mostly tied to data binding and certain legacy visuals) cannot be themed at all.
- **Custom AppSource visuals** may ignore themes or honor only a subset.
- **No version field**: theme JSON is implicitly versioned by the `$schema` URL date suffix.
