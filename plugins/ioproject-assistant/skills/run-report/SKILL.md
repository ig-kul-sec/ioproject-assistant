---
name: run-report
description: Run the daily I&O project status report end to end (Teams, Jira, Confluence, SharePoint -> HTML report, spending report, SharePoint upload, unsent Outlook draft, Confluence draft page). Use when the user asks to run, build or refresh the IO project report.
argument-hint: "[optional period, e.g. 'since 2026-10-12' or 'last 3 days']"
---

# Run the IO Project Assistant report

The user may not be technical. Speak plainly, keep progress updates to one short line each, and never show raw JSON, stack traces or tokens unless they ask.

## 1. Quick pre-flight (stop at the first failure)

Run these checks yourself; if one fails, tell the user in one sentence what is missing and that `/ioproject-assistant:setup` fixes it, then stop.

- Python: `python --version` prints Python 3.10 or newer.
- Tokens file: `test -s "$HOME/.ioassistant/secrets.env"` succeeds. Never print its contents.
- Folder: on Windows, `pwd -W | wc -c` is under 140 (longer paths break the report files).
- Microsoft 365 connector: ToolSearch `select:mcp__claude_ai_Microsoft_365__get_me` returns a tool other than `authenticate`.

## 2. Run the pipeline

Launch the Agent tool with `subagent_type: "ioproject-assistant:orchestrator"`. Prompt: "Run the daily IO Project Assistant pipeline." Add the analysis period only if the user gave one: `$ARGUMENTS`. Say once that a run usually takes 10-20 minutes.

If the user's request is `continue from upload <RUN_ID>` (after a manual upload), skip the first two checks' wait time but still run the pre-flight, then launch the orchestrator with the prompt `Continue from upload <RUN_ID>` and go to step 4.

## 3. Finish the spending report

Never skip this step, also when the orchestrator was launched without this skill. Per the `ioproject-assistant:spend-tracking` skill, take the orchestrator's own Agent result usage (total tokens and duration) and pass it to the renderer, which replaces the `orchestrator` placeholder row in `output/<RUN_ID>/usage.json` (model `claude-opus-5-5`) and re-renders:

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json --orchestrator-tokens <total tokens> --orchestrator-seconds <duration in seconds>
```

The SharePoint copy of the spending report was uploaded before this step; say that only the local copy has the final orchestrator figures.

## 4. Tell the user what they got

A short summary, plain language:
- Where the report is on this computer (`output/<RUN_ID>/<RUN_ID>.html`, full path) and its SharePoint link.
- The Outlook draft link (it is **not sent**; they review and send it themselves).
- The Confluence draft page link.
- Projects needing attention (At risk / Off track), one line each.
- If the SharePoint upload was blocked: say so first, give the full path of `output/<RUN_ID>/upload/<RUN_ID>.html`, ask the user to upload it to the report folder by hand, and offer to continue with the Outlook draft and Confluence page (`/ioproject-assistant:run-report continue from upload <RUN_ID>`). Do not retry the upload yourself.
- Any data gaps, one line each, with what the user can do about them (for example "Jira: token expired; run /ioproject-assistant:setup").
