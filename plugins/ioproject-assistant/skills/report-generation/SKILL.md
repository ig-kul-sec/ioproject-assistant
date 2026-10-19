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
  "sprint": {"name": "", "start": "", "end": "", "tickets": [{"key": "", "url": "", "status": "", "assignee": "", "due": ""}]},
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
      "change": [{"key": "IOSP-1012", "name": "ticket subject", "type": "dates|status|comment", "detail": ""}],
      "create": [{"name": "", "description": "", "start": "", "end": "", "owner": ""}]
    },
    "tickets": [{"key": "", "url": "", "name": "", "status": "", "assignee": "", "start": "", "end": "",
                 "epic": false, "related": [{"key": "", "url": ""}]}],
    "links": {"teams": [{"label": "", "url": ""}], "sharepoint": [], "confluence": [], "jira": []}
  }]
}
```

Per-project section order: 1 Project updates (summary, with ticket links and risks), 2 Jira task updates needed, 3 Project sources, 4 Project meeting chats, 5 Project SharePoint folder, 6 Project Confluence page, 7 Jira tickets (active first, closed or done last). `links.teams`, `links.sharepoint` and `links.confluence` feed sections 4-6; link only the project's own chat, folder and page. Other link types appear under Project sources. The footer shows version (`ioassistant.__version__`), author and the GitHub repository.

`status` drives the management summary (status pills, "Need attention" count). Set it from source evidence only: the roadmap deck's RAG rating first, else Jira (overdue or slipped dates mean At risk or Off track). Leave it empty when no source rates the project; the report then shows "Not rated". Never guess.

`project_manager` and `technical_lead` print under the project name (n/a when unknown). Take them from the roadmap deck's Project review slide, else the Confluence page, else the Jira epic's roles; never guess. `change[].name` is the ticket's subject (summary); the renderer falls back to the project's `tickets` list.

Header links: SharePoint Report Archive Link, Confluence ITSM Parent Page and JIRA ScrumBoard (`brand.JIRA_BOARD_URL`); the Sprint status section starts with a JIRA ScrumBoard Link.

Presentation rules built into the renderer: every table sorts by clicking a column header; dates print as mm/dd (ISO values are kept for sorting); IOSP/RM/COR keys in any text become Jira links; project cards and their sections collapse and expand (plus Collapse all / Expand all); both reports show the SharePoint location (`SHAREPOINT_REPORT_FOLDER_URL`, default the AI Test SharePoint Folder) and the same footer (version, author, GitHub, sectigo.com).

Report style: management layout per the Sectigo brand 2026 (`src/ioassistant/brand.py`, assets bundled in `src/ioassistant/brand/`): summary tiles, projects at a glance, then per-project cards with the top 3 notes (rest collapsed), risks, action items and source links; sprint ticket list and data gaps are collapsed. Palette, fonts and logo come only from the bundled brand files.

The `--compact` build (written to `output/<RUN_ID>/upload/`) is for the connector upload: no embedded fonts or logo image, because file contents must be pasted into the upload call and cannot be reproduced reliably.

Render with `python -m ioassistant.cli report output/<RUN_ID>/data.json`. Output: `output/<RUN_ID>/<RUN_ID>.html` (self-contained, all source links clickable).
