# Clarification Prompts

Reusable question bank for the NLQ Q&A loop in `nlq-dashboard-orchestrator`. Use these when intent is ambiguous. Always prefer one focused question over a wall of questions.

## Data Source (pre-Gate A)

- "Where does the data live? (SQL database, cloud warehouse, Excel/CSV, API, SharePoint)"
- "Do you have a connection string, file path, or workspace ID I should use?"
- "Are there credentials I need to know about, or is this an authenticated session you've already established?"

## Data Model (Gate A)

- "I see N tables. Which ones are relevant to this dashboard?"
- "Which table is the fact table (the one with the metrics you care about)?"
- "How do <table A> and <table B> relate? I'm inferring `<col>` → `<col>` — does that match?"
- "What is the grain of `<fact_table>` — one row per order, order line, transaction, day?"
- "Which column should I use as the primary date for time-based analysis?"
- "Are there role-playing dates (order date vs. ship date vs. delivery date)?"

## Visual Intent (Stage 3)

- "How many visuals do you want? (I can default to 4 — KPI, trend, top-N, breakdown.)"
- "What's the single most important metric for this dashboard?"
- "Should the trend be by day, week, month, quarter, or year?"
- "Top-N visuals — what N? (5, 10, 20)"
- "Any default filters? (year, region, status, customer segment)"
- "Do you need a slicer for users to filter interactively?"

## Layout & Theme

- "Standard 2x2 grid, hero-KPI-row on top, or custom layout?"
- "Theme preference — corporate, modern, minimal, dark — or shall I use the default?"
- "Should the dashboard be on a single page or split across multiple pages?"

## Gate B (Scaffold Readiness)

Always use the verbatim phrasing:

> *"Here is the plan for your dashboard. Are you done with clarifications and ready to scaffold all visuals into the final dashboard? (yes / no — let me know if anything should change)"*

Accept these as affirmative: `yes`, `y`, `proceed`, `go`, `looks good`, `ship it`, `confirmed`, `lgtm`.

Anything else → loop back to Stage 3.
