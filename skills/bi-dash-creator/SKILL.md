---
name: bi-dash-creator
description: Composes a multi-visual Power BI dashboard from already generated reports in the generated-reports folder. This skill should be used only when the user explicitly requests a dashboard combining visuals from previously generated reports. It copies visual.json files, validates semantic model consistency, excludes card/slicer/kpi visuals, arranges up to 4 visuals per page in a 2x2 grid, and saves the output to the generated-dashboards folder with a "Dash" suffix in the project name.
---

# Bi Dash Creator

## Overview

This skill composes a multi-visual Power BI dashboard by combining visuals from previously generated reports in `generated-reports/`. It validates semantic model consistency, filters out non-chart visuals, arranges visuals in a 2x2 grid layout, and outputs a complete PBIP project to `generated-dashboards/`.

## Step 1: Discover Available Visuals

Scan `generated-reports/*/` for all `visual.json` files using the path pattern:

```path
generated-reports/<Name>/<Name>.Report/definition/pages/<pageId>/visuals/<visualId>/visual.json
```

Read the `visual.visualType` field from each file to identify what kind of visual it is.

## Step 2: Filter Excluded Visual Types

Exclude any visuals where `visualType` is one of:

- `cardVisual`
- `slicer`
- `kpi`

Only chart-type visuals (e.g., `clusteredColumnChart`, `lineChart`, `barChart`, `pieChart`, etc.) should be included in the dashboard.

## Step 3: Validate Semantic Model Consistency

- Read each report's `definition.pbir` to get the semantic model reference path (under `datasetReference.byPath.path`)
- Compare TMDL content (`model.tmdl`, `relationships.tmdl`, and all files under `tables/`) across all selected reports
- All visuals in one dashboard **must** share the same semantic model
- If models differ, report which reports are incompatible and stop

## Step 4: Confirm Visuals with User

- Present a table of filtered visuals showing:
  - Report name
  - Visual type
  - Title (if available from the visual's query or objects)
- **Always ask for explicit confirmation before proceeding**
- Do **NOT** proceed without user approval

## Step 5: Assign Positions and Paginate

- Maximum 4 visuals per page
- Use 640x360 edge-to-edge quadrant grid on 1280x720 page:
  - **Top-Left**: x=0, y=0, width=640, height=360
  - **Top-Right**: x=640, y=0, width=640, height=360
  - **Bottom-Left**: x=0, y=360, width=640, height=360
  - **Bottom-Right**: x=640, y=360, width=640, height=360
- If the user uploads a layout image, use vision to determine approximate positions from the image
- If more than 4 visuals, create additional pages

## Step 6: Scaffold Dashboard PBIP

- Run `compose_dashboard.py` to create the dashboard project:

```bash
python skills/bi-dash-creator/scripts/compose_dashboard.py <dashboard-name> \
  --reports-dir generated-reports \
  --output generated-dashboards \
  --reports report1 report2 report3 ...
```

- Output goes to `generated-dashboards/<DashboardName>Dash/`
- All internal references use the `Dash` suffix name
- The script handles:
  1. Visual discovery from specified reports
  2. Filtering excluded visual types
  3. Semantic model validation (relationships must be identical; additive measures across reports are allowed)
  4. Pagination (4 per page, new page for overflow)
  5. Updating each visual.json schema to `2.6.0` and overwriting positions with grid coordinates
  6. Copying the richest semantic model (most TMDL content) as the base, then merging any missing DAX measures from all other source models into the dashboard's table TMDL files (ensures every measure referenced by any visual is present)
  7. Generating all pointer files (.pbip, .pbir, report.json, version.json, pages.json, page.json per page, CY25SU11.json theme)

## Resources

- **Script**: `scripts/compose_dashboard.py` - Main composition script
- **Reference**: `references/dashboard-layout.md` - Grid layout rules and position table
- **Asset**: `assets/position-grid.json` - Machine-readable grid position definitions
- **Sample**: `generated-dashboards/MonthlyUsersDash/` - Use as structural template for output
