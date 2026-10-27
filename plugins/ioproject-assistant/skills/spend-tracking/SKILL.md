---
name: spend-tracking
description: Record per-agent model, tokens and runtime for a run and render the spending report with estimated USD cost.
---

# Spend tracking

`usage.json` is a list; one row per agent (including `orchestrator`):

```json
[{"agent": "teams-collector", "model": "claude-sonnet-5-5", "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}]
```

Take token counts and duration from each Agent tool result's usage block. Prices live in `${CLAUDE_PLUGIN_ROOT}/config/pricing.json` (USD per million tokens). A model with no price yields cost "n/a", never a guess. The orchestrator cannot see its own tokens. It records its wall-clock seconds (start/end timestamps) and a placeholder row, and the session that launched it replaces that row with the usage block of the orchestrator's own Agent result (total tokens and duration), then re-renders the spending report. Never leave the orchestrator out of the report, and never present a placeholder 0 as a measurement.

Render with `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json`. To fill in the orchestrator in the same step, add its Agent result figures: `... spend output/<RUN_ID>/usage.json --orchestrator-tokens <total tokens> --orchestrator-seconds <duration in seconds>` (it replaces the placeholder row and renders; the cost uses the assumed output share in `pricing.json`).
