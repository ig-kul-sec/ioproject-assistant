---
name: report-builder
description: Renders the clickable HTML status report and the spending report from merged run data.
tools: Read, Write, Bash, Skill
model: claude-sonnet-5-5
---

Use the `ioproject-assistant:report-generation` and `ioproject-assistant:spend-tracking` skills. Run:

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli report output/<RUN_ID>/data.json
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json
```

Report any validation error verbatim to the orchestrator; do not patch data yourself.
