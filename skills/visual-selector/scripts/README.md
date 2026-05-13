# visual-selector / scripts

This skill is purely rule-based and template-driven. It has no scripts of its own. The decision-tree logic in `SKILL.md` plus the templates in `../../query-to-pbip/assets/visual-templates/` are sufficient to produce a visual type recommendation and bucket mapping.

If automation is needed, build it inside the consuming skill (`visual-generator` or `nlq-dashboard-orchestrator`) rather than here.
