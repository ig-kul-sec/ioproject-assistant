---
name: report-generation
description: Merged-data schema and rendering of the clickable HTML status report (sprint status + project status).
---

# Report generation

`data.json` schema (all fields optional; missing renders as "n/a"):

```json
{
  "generated_at": "ISO",
  "sprint": {"name": "", "start": "", "end": "", "tickets": [{"key": "", "url": "", "status": "", "assignee": "", "due": ""}]},
  "projects": [{
    "name": "", "status": "On track | At risk | Off track", "notes": [], "progress": "", "timeline": "", "dates": {"start": "", "end": ""},
    "action_items": [{"text": "", "owner": "", "due": ""}], "risks": [],
    "links": {"jira": [{"label": "", "url": ""}], "teams": [], "sharepoint": [], "confluence": []}
  }],
  "gaps": []
}
```

Per-project fields used by the per-project view (all optional; `jira_base_url` defaults to https://projects.sectigo.net/browse/):

```json
{
  "jira_base_url": "https://projects.sectigo.net/browse/",
  "projects": [{
    "summary": [{"text": "", "tickets": ["IOSP-1012"]}],
    "jira_updates": {
      "change": [{"key": "IOSP-1012", "type": "dates|status|comment", "detail": ""}],
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

Report style: management layout per the Sectigo brand 2026 (`src/ioassistant/brand.py`, assets bundled in `src/ioassistant/brand/`): summary tiles, projects at a glance, then per-project cards with the top 3 notes (rest collapsed), risks, action items and source links; sprint ticket list and data gaps are collapsed. Palette, fonts and logo come only from the bundled brand files.

Render with `python -m ioassistant.cli report output/<RUN_ID>/data.json`. Output: `output/<RUN_ID>/<RUN_ID>.html` (self-contained, all source links clickable).
