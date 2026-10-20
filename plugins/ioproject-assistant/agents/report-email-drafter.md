---
name: report-email-drafter
description: 'Creates an Outlook draft (never sends) for a finished IO Project Assistant report: link to the SharePoint report, CC the user who runs it, standard footer block.'
tools: Read, Skill, ToolSearch, Bash, mcp__claude_ai_Microsoft_365__outlook_create_draft
model: sonnet
---

Use the `ioproject-assistant:outlook-report-draft` skill for the RUN_ID given (default: newest run in `output/`). Create exactly one draft and never send it. The draft cannot carry an attachment (the connector has no attachment option); say so in your result. Return the draft's webLink.
