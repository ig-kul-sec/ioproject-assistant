---
name: spend-tracking
description: Record per-agent model, tokens and runtime for a run and render the spending report with estimated USD cost.
---

# Spend tracking

`usage.json` is a list; one row per agent (including `orchestrator`):

```json
[{"agent": "teams-collector", "model": "claude-sonnet-5-5", "input_tokens": 0, "output_tokens": 0, "seconds": 0.0}]
```

Take token counts and duration from each Agent tool result's usage block. Prices live in `config/pricing.json` (USD per million tokens). A model with no price yields cost "n/a", never a guess. Render with `python -m ioassistant.cli spend output/<RUN_ID>/usage.json`.
