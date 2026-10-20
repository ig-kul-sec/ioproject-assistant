---
name: report-generation
description: Merged-data schema and rendering of the clickable HTML status report (sprint status + project status).
---

# Report generation

`data.json` schema (all fields optional; missing renders as "n/a"):

```json
{
  "generated_at": "ISO",
  "window": {"from": "ISO with offset", "to": "ISO with offset"},
  "sprint": {"name": "", "start": "", "end": "", "tickets": [{"key": "", "url": "", "name": "ticket subject", "status": "", "assignee": "", "due": ""}]},
  "past_sprint": null,
  "projects": [{
    "name": "", "status": "On track | At risk | Off track", "notes": [], "progress": "", "timeline": "", "dates": {"start": "", "end": ""},
    "action_items": [{"text": "", "owner": "", "due": ""}], "risks": [],
    "links": {"jira": [{"label": "", "url": ""}], "teams": [], "sharepoint": [], "confluence": []}
  }],
  "gaps": []
}
```

`window` is the analysis period, printed at the top as `Analysis period: yyyy.mm.dd - yyyy.mm.dd hh:mm EDT` (24-hour clock, America/New_York, zone label EST/EDT as in force). `generated_at` prints as `Generated: yyyy.mm.dd hh:mm EDT`.

Per-project fields used by the per-project view (all optional; `jira_base_url` defaults to https://projects.sectigo.net/browse/):

```json
{
  "jira_base_url": "https://projects.sectigo.net/browse/",
  "projects": [{
    "project_manager": "Name", "technical_lead": "Name",
    "summary": [{"text": "", "tickets": ["IOSP-1012"]}],
    "jira_updates": {
      "change": [{"key": "IOSP-1012", "name": "ticket subject", "type": "dates|status|comment", "detail": "what to do", "reason": "why, with the evidence and its source"}],
      "create": [{"name": "", "description": "what the ticket is for", "reason": "why it is needed, with the evidence and its source", "start": "", "end": "", "owner": ""}]
    },
    "tickets": [{"key": "", "url": "", "name": "", "status": "", "sprint": "", "assignee": "", "start": "", "end": "",
                 "epic": false, "related": [{"key": "", "url": ""}]}],
    "links": {"teams": [{"label": "", "url": ""}], "sharepoint": [], "confluence": [], "jira": []}
  }]
}
```

`past_sprint` has the same shape as `sprint`; set it only for a sprint that has ended but is not closed in Jira yet, otherwise leave it null. "Sprint status" then shows two collapsible subsections, Past sprint (not closed yet) first and Current sprint second. A project ticket's `sprint` is its sprint name; when it is missing the report uses the current or past sprint if the key is in that sprint's ticket list, else "n/a".

Write Jira keys in full in every text field ("IOSP-1004 and IOSP-1005", never "IOSP-1004/1005"), so each key becomes a link. The renderer also links shorthand lists when it meets them.

`jira_updates.create` has one entry per ticket. An action item that names several deliverables or separate vendors/teams (for example "Rubrik and Oracle support cases") becomes one entry for each, never one combined line.

Daily Ops operational health and incidents (top-level `non_project`, from the Daily Ops Standup only): items discussed at the standup that belong to no project, such as system health, incidents, problems, issues, changes and maintenance. They render as the "Daily Ops operational health and incidents" section after the project cards and before Sprint status. Rows are newest first, with columns Date, Type, Item, Status / next step, Update by, Owner, Jira tickets and Source, and a "Daily Ops items" count tile in the summary.

```json
{"non_project": [{"date": "YYYY-MM-DD (latest standup it was discussed)", "type": "Incident | Problem | Issue | Change | Maintenance | Other",
  "title": "", "detail": "", "status": "current state or next step",
  "reported_by": "person who gave the latest update at the standup (null if unknown)", "owner": null,
  "tickets": [{"key": "IOSP-123", "url": "https://projects.sectigo.net/browse/IOSP-123", "status": "In Progress"}],
  "source": {"label": "Standup 2026-10-14 · closing recap (13:24 UTC)", "url": ""}}]}
```

`reported_by` is the speaker or chat author who gave the update. It is never the meeting assistant (Facilitator) and never the person who summarized; when only a bot recap mentions the item and no one is named, use null. `tickets` lists related Jira tickets only: tickets named at the standup, plus tickets the Jira collector found clearly about the same item, each with its current status. Plain key strings are also accepted.

Type meanings: **Incident** = an unplanned outage or degradation being handled now; **Problem** = a recurring or root-cause item (RCA, repeat issues); **Issue** = a blocker or risk outside any project; **Change** = a planned change or deployment (RM/COR change tickets); **Maintenance** = routine or scheduled operational work (backups, patching, maintenance windows); **Other** = anything else. Never put a project's item here, and never invent an owner or status (null renders as n/a).

Per-project section order: 1 Project updates (summary, with ticket links and risks), 2 Jira task updates needed, 3 Project sources, 4 Project meeting chats, 5 Project SharePoint folder, 6 Project Confluence page, 7 Jira tickets (active first, closed or done last). `links.teams`, `links.sharepoint` and `links.confluence` feed sections 4-6; link only the project's own chat, folder and page. Other link types appear under Project sources. The footer shows version (`ioassistant.__version__`), author and the GitHub repository.

`status` drives the management summary (status pills, "Need attention" count). Set it from source evidence only: the roadmap deck's RAG rating first, else Jira (overdue or slipped dates mean At risk or Off track). Leave it empty when no source rates the project; the report then shows "Not rated". Never guess.

`project_manager` and `technical_lead` print under the project name (n/a when unknown). Take them from the roadmap deck's Project review slide, else the Confluence page, else the Jira epic's roles; never guess. `change[].name` is the ticket's subject (summary); the renderer falls back to the project's `tickets` list.

Header links: SharePoint Report Archive Link, Confluence ITSM Parent Page and JIRA ScrumBoard (`brand.JIRA_BOARD_URL`); the Sprint status section starts with a JIRA ScrumBoard Link.

Presentation rules built into the renderer: every table sorts by clicking a column header; dates print as mm/dd (ISO values are kept for sorting); IOSP/RM/COR keys in any text become Jira links; project cards and their sections collapse and expand (plus Collapse all / Expand all); both reports show the SharePoint location (`SHAREPOINT_REPORT_FOLDER_URL`, default the AI Test SharePoint Folder) and the same footer (version, author, GitHub, sectigo.com).

Report style: management layout per the Sectigo brand 2026 (`${CLAUDE_PLUGIN_ROOT}/src/ioassistant/brand.py`, assets bundled in `${CLAUDE_PLUGIN_ROOT}/src/ioassistant/brand/`): summary tiles, projects at a glance, then per-project cards with the top 3 notes (rest collapsed), risks, action items and source links; sprint ticket list and data gaps are collapsed. Palette, fonts and logo come only from the bundled brand files.

The `--compact` build (written to `output/<RUN_ID>/upload/`) is for the connector upload: no embedded fonts or logo image, because file contents must be pasted into the upload call and cannot be reproduced reliably.

Render with `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli report output/<RUN_ID>/data.json`. Output: `output/<RUN_ID>/<RUN_ID>.html` (self-contained, all source links clickable).
