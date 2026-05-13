#!/usr/bin/env python3
"""
apply_theme.py — Apply a theme to a generated PBIP project.

Steps:
  1. Validate the theme JSON against minimal schema rules
  2. Copy the theme into <ProjectName>.Report/StaticResources/SharedResources/BaseThemes/
  3. Patch <ProjectName>.Report/definition/report.json to reference the new theme
  4. Optionally apply color overrides (--primary, --secondary, --accent)
  5. Optionally embed a logo file as a RegisteredResource

Usage:
    python apply_theme.py <ProjectDir> --theme corporate
    python apply_theme.py <ProjectDir> --theme-file ./my-theme.json
    python apply_theme.py <ProjectDir> --theme dark --primary "#19F5E2" --logo ./logo.png
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

HEX_RE = re.compile(r"^#[0-9A-Fa-f]{6}$")

BUILTIN_THEMES = {"corporate", "modern", "minimal", "dark"}


TEXT_CLASSES = {
    "callout", "title", "header", "label", "lightLabel", "largeLabel",
    "smallLabel", "semiboldLabel", "boldLabel", "largeLightLabel",
    "circularGauge", "colorLink",
}

STRUCTURAL_COLOR_SLOTS = (
    "background", "secondaryBackground",
    "foreground", "secondaryForeground",
    "tableAccent",
)

SENTIMENT_DIVERGING_SLOTS = (
    "good", "neutral", "bad",
    "maximum", "center", "minimum", "null",
)


def _check_visual_styles_color_wrapping(visual_styles: dict, errors: list[str]) -> None:
    """Walk visualStyles and flag any bare hex strings used as colors.

    Per MS docs (report-themes-create-custom), color values inside
    `visualStyles` must be wrapped as `{ "solid": { "color": "#hex" } }`,
    a `{ "expr": { "ThemeDataColor": ... } }` expression, or a gradient
    wrapper. Bare hex strings at color-property keys are silently ignored
    by Power BI.

    The walker treats the *child* of any recognized wrapper key (`solid`,
    `expr`, `linearGradient`, `colorPalette`) as authoritative \u2014 hex
    strings inside those subtrees are correct, not bugs.
    """
    color_property_keys = {"color", "fontColor", "borderColor", "fill", "lineColor", "labelColor"}
    wrapper_keys = {"solid", "expr", "linearGradient", "colorPalette"}

    def walk(node, path: str, inside_wrapper: bool) -> None:
        if isinstance(node, dict):
            for k, v in node.items():
                new_path = f"{path}.{k}" if path else k
                if k in color_property_keys and isinstance(v, str) and HEX_RE.match(v) and not inside_wrapper:
                    errors.append(
                        f"`visualStyles.{new_path}` is a bare hex string `{v}`. "
                        f"Wrap as `{{ \"solid\": {{ \"color\": \"{v}\" }} }}`."
                    )
                else:
                    walk(v, new_path, inside_wrapper or k in wrapper_keys)
        elif isinstance(node, list):
            for i, item in enumerate(node):
                walk(item, f"{path}[{i}]", inside_wrapper)

    walk(visual_styles, "", inside_wrapper=False)


def validate_theme(theme: dict) -> list[str]:
    """Return a list of validation errors. Empty list = valid.

    Aligned with Microsoft's report-theme schema:
    https://learn.microsoft.com/power-bi/create-reports/report-themes-create-custom
    """
    errors: list[str] = []
    if not isinstance(theme, dict):
        return ["Theme is not a JSON object"]

    # 1. name
    name = theme.get("name")
    if not isinstance(name, str) or not name.strip():
        errors.append("Missing or empty `name`")

    # 2. dataColors >= 8 valid hex
    data_colors = theme.get("dataColors")
    if not isinstance(data_colors, list) or len(data_colors) < 8:
        errors.append("`dataColors` must be an array of at least 8 hex strings")
    else:
        for i, c in enumerate(data_colors):
            if not isinstance(c, str) or not HEX_RE.match(c):
                errors.append(f"`dataColors[{i}]` is not a 6-digit hex string: {c!r}")

    # 3. Structural + sentiment/diverging slots — hex when present
    for color_field in STRUCTURAL_COLOR_SLOTS + SENTIMENT_DIVERGING_SLOTS:
        v = theme.get(color_field)
        if v is not None and (not isinstance(v, str) or not HEX_RE.match(v)):
            errors.append(f"`{color_field}` is not a valid hex string: {v!r}")

    # 4. textClasses — known names, valid fontSize range, valid color hex
    text_classes = theme.get("textClasses")
    if text_classes is not None:
        if not isinstance(text_classes, dict):
            errors.append("`textClasses` must be an object")
        else:
            for class_name, spec in text_classes.items():
                if class_name not in TEXT_CLASSES:
                    errors.append(
                        f"`textClasses.{class_name}` is not a known text class. "
                        f"Valid classes: {sorted(TEXT_CLASSES)}"
                    )
                if not isinstance(spec, dict):
                    errors.append(f"`textClasses.{class_name}` must be an object")
                    continue
                fs = spec.get("fontSize")
                if fs is not None:
                    if not isinstance(fs, int) or fs < 6 or fs > 72:
                        errors.append(
                            f"`textClasses.{class_name}.fontSize` must be an integer in [6, 72]; got {fs!r}"
                        )
                col = spec.get("color")
                if col is not None and (not isinstance(col, str) or not HEX_RE.match(col)):
                    errors.append(
                        f"`textClasses.{class_name}.color` is not a valid hex string: {col!r}"
                    )

    # 5. visualStyles — must be an object; colors must be wrapped, not bare hex
    visual_styles = theme.get("visualStyles")
    if visual_styles is not None:
        if not isinstance(visual_styles, dict):
            errors.append("`visualStyles` must be an object")
        else:
            _check_visual_styles_color_wrapping(visual_styles, errors)

    return errors


def apply_overrides(theme: dict, primary: str | None, secondary: str | None, accent: str | None) -> dict:
    """Apply brand overrides across all consistent surfaces.

    Per SKILL.md \u00a7Step 3:
      1. dataColors[0..2] \u2190 primary/secondary/accent
      2. tableAccent     \u2190 primary
      3. textClasses.title.color \u2190 primary (so visual titles match brand)
      4. textClasses.callout.color \u2190 primary (so card big-numbers match brand)
    """
    if not (primary or secondary or accent):
        return theme
    colors = list(theme.get("dataColors", []))
    while len(colors) < 8:
        colors.append("#888888")
    if primary:
        colors[0] = primary
    if secondary:
        colors[1] = secondary
    if accent:
        colors[2] = accent
    theme["dataColors"] = colors
    if primary:
        theme["tableAccent"] = primary
        text_classes = theme.setdefault("textClasses", {})
        for cls in ("title", "callout"):
            spec = text_classes.get(cls)
            if isinstance(spec, dict):
                spec["color"] = primary
    return theme


def patch_report_json(report_json_path: Path, theme_name: str) -> None:
    with open(report_json_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    base_theme = report.setdefault("themeCollection", {}).setdefault("baseTheme", {})
    base_theme["name"] = theme_name
    base_theme.setdefault("type", "SharedResources")
    base_theme.setdefault("reportVersionAtImport", {
        "visual": "2.4.0",
        "report": "3.0.0",
        "page": "2.3.0",
    })

    resource_packages = report.setdefault("resourcePackages", [])
    shared = next((p for p in resource_packages if p.get("name") == "SharedResources"), None)
    if shared is None:
        shared = {"name": "SharedResources", "type": "SharedResources", "items": []}
        resource_packages.append(shared)
    items = shared.setdefault("items", [])
    existing = next((i for i in items if i.get("type") == "BaseTheme"), None)
    new_entry = {
        "name": theme_name,
        "path": f"BaseThemes/{theme_name}.json",
        "type": "BaseTheme",
    }
    if existing:
        existing.clear()
        existing.update(new_entry)
    else:
        items.append(new_entry)

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def embed_logo(report_dir: Path, report_json_path: Path, logo_path: Path) -> None:
    if not logo_path.exists():
        print(f"[warn] logo file not found: {logo_path}", file=sys.stderr)
        return
    registered_dir = report_dir / "StaticResources" / "RegisteredResources"
    registered_dir.mkdir(parents=True, exist_ok=True)
    dest = registered_dir / logo_path.name
    shutil.copy2(logo_path, dest)

    with open(report_json_path, "r", encoding="utf-8") as f:
        report = json.load(f)

    resource_packages = report.setdefault("resourcePackages", [])
    reg = next((p for p in resource_packages if p.get("name") == "RegisteredResources"), None)
    if reg is None:
        reg = {"name": "RegisteredResources", "type": "RegisteredResources", "items": []}
        resource_packages.append(reg)
    items = reg.setdefault("items", [])
    entry = {
        "name": logo_path.stem,
        "path": logo_path.name,
        "type": "Image",
    }
    if not any(i.get("name") == entry["name"] for i in items):
        items.append(entry)

    with open(report_json_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)


def find_report_dir(project_dir: Path) -> Path:
    matches = list(project_dir.glob("*.Report"))
    if not matches:
        raise FileNotFoundError(f"No *.Report directory under {project_dir}")
    return matches[0]


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply a theme to a PBIP project")
    parser.add_argument("project_dir", help="Path to the PBIP project directory")
    parser.add_argument("--theme", choices=sorted(BUILTIN_THEMES),
                        help="Built-in theme preset name")
    parser.add_argument("--theme-file", help="Path to a custom theme JSON file")
    parser.add_argument("--primary", help="Override primary color (hex, e.g. #1F3864)")
    parser.add_argument("--secondary", help="Override secondary color")
    parser.add_argument("--accent", help="Override accent color")
    parser.add_argument("--logo", help="Path to a logo image to embed")
    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        print(f"Project directory not found: {project_dir}", file=sys.stderr)
        return 2

    if args.theme_file:
        theme_src = Path(args.theme_file).resolve()
    elif args.theme:
        theme_src = Path(__file__).resolve().parent.parent / "assets" / "themes" / f"{args.theme}.json"
    else:
        print("Specify either --theme <preset> or --theme-file <path>", file=sys.stderr)
        return 2

    if not theme_src.exists():
        print(f"Theme file not found: {theme_src}", file=sys.stderr)
        return 2

    with open(theme_src, "r", encoding="utf-8") as f:
        theme = json.load(f)

    theme = apply_overrides(theme, args.primary, args.secondary, args.accent)
    errors = validate_theme(theme)
    if errors:
        print("Theme validation failed:", file=sys.stderr)
        for e in errors:
            print(f"  - {e}", file=sys.stderr)
        return 1

    report_dir = find_report_dir(project_dir)
    base_themes_dir = report_dir / "StaticResources" / "SharedResources" / "BaseThemes"
    base_themes_dir.mkdir(parents=True, exist_ok=True)
    theme_name = theme["name"]
    theme_dest = base_themes_dir / f"{theme_name}.json"
    with open(theme_dest, "w", encoding="utf-8") as f:
        json.dump(theme, f, indent=2)

    report_json = report_dir / "definition" / "report.json"
    if not report_json.exists():
        print(f"report.json not found at {report_json}", file=sys.stderr)
        return 1
    patch_report_json(report_json, theme_name)

    if args.logo:
        embed_logo(report_dir, report_json, Path(args.logo).resolve())

    print(f"[ok] Applied theme `{theme_name}` to {project_dir}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
