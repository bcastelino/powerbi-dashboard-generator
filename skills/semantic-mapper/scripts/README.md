# semantic-mapper / scripts

This skill is documentation-driven. The Python helpers it relies on live in the orchestrator skill:

| Helper | Location | Purpose |
|---|---|---|
| `generate_tmdl_scripts.py` | `../../query-to-pbip/scripts/generate_tmdl_scripts.py` | Consolidates split TMDL into a single `TMDLScripts/power-bi-semantic-model.tmdl` |
| `scaffold_pbip.py` | `../../query-to-pbip/scripts/scaffold_pbip.py` | Scaffolds the PBIP directory + writes TMDL into it |

When invoked through the full pipeline (`nlq-dashboard-orchestrator` or `query-to-pbip`), these scripts are called for you. When using `semantic-mapper` standalone, invoke them directly from the `query-to-pbip` location.
