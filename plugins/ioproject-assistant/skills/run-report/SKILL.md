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
- Folder access: run `mkdir -p output && pwd -W`, then use the Glob tool (pattern `*`, path `<that folder>/output`) and the Read tool (first line only) on `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`. An empty `output` folder is fine. If either call answers that reads outside the working directories are blocked (setting `permissions.blockReadsOutsideWorkingDirectories`), the run would lose its config and roster files and could not upload the report. Stop and tell the user: "Claude is not allowed to read <the folder that was refused>. Type `/add-dir <that folder>`, or reopen Claude in the report folder, then run the report again." Do not change any permission setting yourself.

## 2. Run the pipeline

Launch the Agent tool with `subagent_type: "ioproject-assistant:orchestrator"`. Prompt: "Run the daily IO Project Assistant pipeline." Add the analysis period only if the user gave one: `$ARGUMENTS`. Say once that a run usually takes 10-20 minutes.

If the user's request is `continue from upload <RUN_ID>` (after a manual upload), skip the first two checks' wait time but still run the pre-flight, then launch the orchestrator with the prompt `Continue from upload <RUN_ID>`, do step 3 for its resume row, and go to step 4.

## 3. Finish the spending report

Never skip this step, also when the orchestrator was launched without this skill. Per the `ioproject-assistant:spend-tracking` skill, take the orchestrator's own Agent result usage (total tokens and duration) and pass it to the renderer, which replaces the `orchestrator` placeholder row in `output/<RUN_ID>/usage.json` (model `claude-opus-5-5`) and re-renders:

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json --orchestrator-tokens <total tokens> --orchestrator-seconds <duration in seconds>
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json --compact
```

The first command fills the row and renders the local report; the second rebuilds the compact copy in `output/<RUN_ID>/upload/`. In resume mode add `--orchestrator-row "orchestrator (resume)"` to the first command (the first run's row stays). Always give the path with the run folder in it, not a bare `usage.json`.

The SharePoint copy of the spending report was uploaded before the orchestrator's figures existed, so refresh it when the main report is on SharePoint (the upload succeeded, or in resume mode `Continue from upload` verified it): launch `ioproject-assistant:sharepoint-collector` in upload mode for `output/<RUN_ID>/upload/<RUN_ID>_spending.html` with "Replace mode: this is the run's own spending report, refreshed with the final figures; replace only that file." Do not retry a denied or failed refresh; say that only the local copy has the final figures. If the main report was never uploaded (blocked upload), skip the refresh and say the same. The refresh itself is not added to the spending report.

## 4. Tell the user what they got

A short summary, plain language:
- Where the report is on this computer (`output/<RUN_ID>/<RUN_ID>.html`, full path) and its SharePoint link.
- The Outlook draft link (it is **not sent**; they review and send it themselves).
- The Confluence draft page link.
- Projects needing attention (At risk / Off track), one line each.
- If the SharePoint upload was blocked: say so first, give the full path of `output/<RUN_ID>/upload/<RUN_ID>.html`, ask the user to upload it to the report folder by hand, and offer to continue with the Outlook draft and Confluence page (`/ioproject-assistant:run-report continue from upload <RUN_ID>`). If the reason mentions reads outside the working directories, tell them to type `/add-dir <the folder that holds output>` first, because the next run would be blocked the same way. Do not retry the upload yourself.
- Any data gaps, one line each, with what the user can do about them (for example "Jira: token expired; run /ioproject-assistant:setup").
