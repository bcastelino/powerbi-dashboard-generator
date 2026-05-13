# project-packager / scripts

This skill is implemented by two scripts that live alongside `query-to-pbip`:

| Script | Location | Purpose |
|---|---|---|
| `scaffold_pbip.py` | `../../query-to-pbip/scripts/scaffold_pbip.py` | Scaffold the PBIP directory + pointer files |
| `package_pbip.py` | `../../query-to-pbip/scripts/package_pbip.py` | Validate + zip the PBIP archive |

Run them directly from the `query-to-pbip` location. They are intentionally shared (not duplicated) so the entire pipeline produces byte-identical artifacts regardless of entry point.
