---
name: run-leadership-updates
description: Run the IO Projects Leadership Updates pipeline (main IO Project Assistant reports of a period + the I&O Project Roadmap deck -> HTML report with the deck's previous information beside a proposal for new statuses, SharePoint upload, unsent Outlook draft to the PMO, Confluence draft page). Use when the user asks for the leadership updates, the roadmap deck update proposal or the weekly project update for leadership.
argument-hint: "[optional period, e.g. 'since 2026-10-30' or 'last 14 days'; default: the last 7 days]"
---

# Run the IO Projects Leadership Updates

The user may not be technical. Speak plainly, keep progress updates to one short line each, and never show raw JSON, stack traces or tokens unless they ask.

This pipeline never reads Teams, Jira or Confluence itself. Its sources are the **main IO Project Assistant reports** already in `output/` for the period and the **I&O Project Roadmap deck**. It never changes the deck: it only proposes new statuses and text.

## 1. Quick pre-flight (stop at the first failure)

If one check fails, tell the user in one sentence what is missing and that `/ioproject-assistant:setup` fixes it (for the reports: run `/ioproject-assistant:run-report` first), then stop.

- Python: `python --version` prints Python 3.10 or newer.
- Tokens file: `test -s "$HOME/.ioassistant/secrets.env"` succeeds (the Confluence page needs it). Never print its contents.
- Folder: on Windows, `pwd -W | wc -c` is under 140.
- Microsoft 365 connector: ToolSearch `select:mcp__claude_ai_Microsoft_365__get_me` returns a tool other than `authenticate`.
- Main reports: `ls output | grep -c '^IOProjectAssistantReport_'` is above 0 (the orchestrator checks the period itself).
- Folder access: same check as `run-report` (`mkdir -p output && pwd -W`, Glob on `<that folder>/output`, Read of the first line of `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`). If reads outside the working directories are blocked, tell the user: "Claude is not allowed to read <folder>. Type `/add-dir <folder>`, or reopen Claude in the report folder, then run it again." Do not change any permission setting.

## 2. Run the pipeline

Launch the Agent tool with `subagent_type: "ioproject-assistant:orchestrator-leadership"`. Prompt: "Run the IO Projects Leadership Updates pipeline." Add the analysis period only if the user gave one: `$ARGUMENTS`. Say once that a run usually takes 10-20 minutes.

If the request is `continue from upload <RUN_ID>` (after a manual upload), run the pre-flight and launch the orchestrator with the prompt `Continue from upload <RUN_ID>`.

## 3. Finish the spending report

Never skip this step, also when the orchestrator was launched without this skill. Same rules as `run-report` (skill `ioproject-assistant:spend-tracking`): take the orchestrator's own Agent result usage (total tokens and duration) and pass it to the renderer, which replaces the `orchestrator` placeholder row in `output/<RUN_ID>/usage.json` (model `claude-opus-5-5`) and re-renders:

```bash
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json --orchestrator-tokens <total tokens> --orchestrator-seconds <duration in seconds>
PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli spend output/<RUN_ID>/usage.json --compact
```

The first command fills the row and renders the local report; the second rebuilds the compact copy in `output/<RUN_ID>/upload/`. In resume mode add `--orchestrator-row "orchestrator (resume)"` to the first command. Always give the path with the run folder in it.

The SharePoint copy of the spending report was uploaded before the orchestrator's figures existed, so refresh it when the main report is on SharePoint (the upload succeeded, or in resume mode `Continue from upload` verified it): launch `ioproject-assistant:collector-sharepoint` in upload mode for `output/<RUN_ID>/upload/<RUN_ID>_spending.html` with "Replace mode: this is the run's own spending report, refreshed with the final figures; replace only that file." Give its byte count (`wc -c`). Do not retry a denied or failed refresh; say that only the local copy has the final figures. If the main report was never uploaded (blocked upload), skip the refresh and say the same. The refresh itself is not added to the spending report.

## 4. Tell the user what they got

A short summary, plain language:
- Where the report is on this computer (`output/<RUN_ID>/<RUN_ID>.html`, full path) and its SharePoint link, and the spending report's SharePoint link with the run's estimated cost.
- The Outlook draft link (it is **not sent**; To the PMO, CC the user; they review and send it themselves) and the Confluence draft page link.
- Per project whose status the proposal changes: one line `Project: Off track -> At risk (why)`. Then the count of projects with no change.
- If the SharePoint upload was blocked: say so first, give the full path of `output/<RUN_ID>/upload/<RUN_ID>.html`, ask the user to upload it to the report folder by hand, and offer `/ioproject-assistant:run-leadership-updates continue from upload <RUN_ID>`. If the reason mentions reads outside the working directories, tell them to type `/add-dir <the folder that holds output>` first.
- Any data gaps, one line each, with what the user can do about them (for example "no main report on 11/03: run the report that day next time").

## Names and files

- `RUN_ID = IOProjectLeadershipUpdates_<yyyymmdd>_<hhmm>` (America/New_York clock; `DEV_` prefix when the plugin runs from the DEV branch). The report, the SharePoint file, the Outlook subject and the Confluence title all follow from it:
  - file `IOProjectLeadershipUpdates_20261105_1008.html` in the SharePoint report folder (the same folder as the main report), and next to it the spending report `IOProjectLeadershipUpdates_20261105_1008_spending.html`
  - Outlook subject `IO Projects Leadership Updates 20261105 1008`
  - Confluence page `TEST: IO Projects Leadership Updates 20261105 1008 (Draft)` under PMO AI Agent Factory > IO Project Assistant (page 110166017)
- Run folder `output/<RUN_ID>/`: `reports.json` (digest of the main reports), `deck.json` (the deck as read), `data.json` (merged data), `usage.json` (per-agent model, tokens and seconds), `<RUN_ID>.html`, `<RUN_ID>_spending.html`, `upload/` (compact copies: report, spending report, `_email.html`, `_confluence.xhtml`).

## `data.json` schema (leadership)

All fields are optional except `projects[].name`; a missing value renders as "n/a". Never invent facts.

```json
{
  "generated_at": "ISO with offset",
  "window": {"from": "ISO with offset", "to": "ISO with offset"},
  "deck": {"url": "", "slides": "5-9", "modified": "yyyy-mm-dd or null"},
  "reports": [{"run_id": "IOProjectAssistantReport_20261105_1008", "generated_at": "ISO", "url": "SharePoint link"}],
  "projects": [{
    "name": "name on the deck", "slide": 5, "report_names": ["name in the main reports"],
    "key_changes": [{"text": "", "date": "yyyy-mm-dd", "source": "run id of the main report"}],
    "resources": {"epics": [{"key": "IOSP-471", "url": "", "name": "", "status": ""}],
                  "chats": [{"label": "", "url": ""}], "confluence": [], "sharepoint": [], "jira": [], "other": []},
    "deck": {"status": "Off Track", "schedule": "R", "scope": "G", "cost": "G", "pm": "", "tl": "",
             "accomplishments": [], "whats_next": [], "issues": [], "risks": [], "dependencies": [], "milestones": []},
    "proposal": {"same fields as deck": ""},
    "rationale": "why the proposal differs from the deck, with the evidence and its source (empty when it does not)"
  }],
  "other_projects": [{"name": "", "status": "", "summary": ["up to 3 lines"]}],
  "gaps": []
}
```

- `deck` is the deck exactly as read (left side). `proposal` starts as a copy of it and changes only where the main reports of the period give evidence (right side). Statuses are `On track`, `At risk`, `Off track`, `Paused` (spelling and hyphens as on the deck are accepted); RAG letters are `G`, `Y`, `R` or null.
- The report marks every text bullet the proposal adds (New) or replaces (Superseded), tags each row Updated / No change, and counts changed blocks per project.
- `key_changes[].source` is a main report run id: the report links it to that report on SharePoint.
- `other_projects` are projects in the newest main report that are not on the deck; the page lists them under "Not on the deck".
- The project list, the contents rail and the three tabs (Project updates, Sources, Data gaps) are built by the renderer; write only the data. Each project card shows, in this order: 1 key changes of the period, 2 the deck's previous information beside the proposal, 3 key project resources (two columns: Jira epics, Confluence, SharePoint, Project chats, Other links). At risk is orange, Off track red, Paused dashed; the header title is red.

Render: `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli leadership-report output/<RUN_ID>/data.json` (add `--compact` for the upload copy). Digest: `... leadership-collect output/<RUN_ID> --from <ISO> --to <ISO>`. Outlook body and Confluence body: `... email|confluence output/<RUN_ID>/data.json` (the run folder name selects the leadership content).

Roadmap deck project names and the words that identify the same project in the main reports live in `${CLAUDE_PLUGIN_ROOT}/config/leadership-projects.json`; extend it when the deck gets a new project.
