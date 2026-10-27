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
  "sprint": {"id": 0, "name": "", "start": "", "end": "", "tickets": [{"key": "", "url": "", "name": "ticket subject", "status": "", "assignee": "", "due": ""}]},
  "past_sprints": [],
  "projects": [{
    "name": "", "status": "On track | At risk | Off track", "notes": [], "progress": "", "timeline": "", "dates": {"start": "", "end": ""},
    "action_items": [{"text": "", "owner": "", "due": ""}], "risks": [],
    "links": {"jira": [{"label": "", "url": ""}], "teams": [], "sharepoint": [], "confluence": []}
  }],
  "gaps": []
}
```

`window` is the analysis period, printed at the top as `Analysis period: yyyy.mm.dd - yyyy.mm.dd hh:mm EDT` (24-hour clock, America/New_York, zone label EST/EDT as in force). `generated_at` prints as `Generated: yyyy.mm.dd hh:mm EDT`.

Per-project fields used by the per-project view (all optional; `jira_base_url` defaults to https://sectigo.atlassian.net/browse/):

```json
{
  "jira_base_url": "https://sectigo.atlassian.net/browse/",
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

`past_sprints` is a list (oldest first) of objects shaped like `sprint`, one for every sprint that has ended but is not closed in Jira yet; leave it empty when there are none. (A single `past_sprint` object is still accepted.) The "JIRA tickets" section (after "Sprint charts") then shows one collapsible subsection per past sprint, titled "Past sprint <name> (not closed yet)", followed by "Current sprint <name>". A project ticket's `sprint` is its sprint name; when it is missing the report uses the current or a past sprint if the key is in that sprint's ticket list, else "n/a".

Write Jira keys in full in every text field ("IOSP-1004 and IOSP-1005", never "IOSP-1004/1005"), so each key becomes a link. The renderer also links shorthand lists when it meets them.

`jira_updates.create` has one entry per ticket. An action item that names several deliverables or separate vendors/teams (for example "Rubrik and Oracle support cases") becomes one entry for each, never one combined line.

Daily Ops operational health and incidents (top-level `non_project`, from the Daily Ops Standup only): items discussed at the standup that belong to no project, such as system health, incidents, problems, issues, changes and maintenance. They render as the "Daily Ops operational health and incidents" section after the project cards and before the Sprint management tab. Rows are newest first, with columns Date, Type, Item, Status / next step, Update by, Owner, Jira tickets and Source, and a "Daily Ops items" count tile in the summary.

```json
{"non_project": [{"date": "YYYY-MM-DD (latest standup it was discussed)", "type": "Incident | Problem | Issue | Change | Maintenance | Other",
  "title": "", "detail": "", "status": "current state or next step",
  "reported_by": "person who gave the latest update at the standup (null if unknown)", "owner": null,
  "tickets": [{"key": "IOSP-123", "url": "https://sectigo.atlassian.net/browse/IOSP-123", "status": "In Progress"}],
  "source": {"label": "Standup 2026-10-14 · closing recap (13:24 UTC)", "url": ""}}]}
```

`reported_by` is the speaker or chat author who gave the update. It is never the meeting assistant (Facilitator) and never the person who summarized; when only a bot recap mentions the item and no one is named, use null. `tickets` lists related Jira tickets only: tickets named at the standup, plus tickets the Jira collector found clearly about the same item, each with its current status. Plain key strings are also accepted.

Type meanings: **Incident** = an unplanned outage or degradation being handled now; **Problem** = a recurring or root-cause item (RCA, repeat issues); **Issue** = a blocker or risk outside any project; **Change** = a planned change or deployment (RM/COR change tickets); **Maintenance** = routine or scheduled operational work (backups, patching, maintenance windows); **Other** = anything else. Never put a project's item here, and never invent an owner or status (null renders as n/a).

Per-project section order: 1 Project updates (summary, with ticket links and risks), 2 Jira task updates needed, 3 Project sources, 4 Project meeting chats, 5 Project SharePoint folder, 6 Project Confluence page, 7 Jira tickets (active first, closed or done last). `links.teams`, `links.sharepoint` and `links.confluence` feed sections 4-6; link only the project's own chat, folder and page. Other link types appear under Project sources. The footer shows version (`ioassistant.__version__`), author and the GitHub repository.

`status` drives the management summary (status pills, "Need attention" count). Set it from source evidence only: the roadmap deck's RAG rating first, else Jira (overdue or slipped dates mean At risk or Off track). Leave it empty when no source rates the project; the report then shows "Not rated". Never guess.

`project_manager` and `technical_lead` print under the project name (n/a when unknown). Take them from the roadmap deck's Project review slide, else the Confluence page, else the Jira epic's roles; never guess. `change[].name` is the ticket's subject (summary); the renderer falls back to the project's `tickets` list.

"Sprint charts" holds at-a-glance tiles, Tickets by status, Tickets by team and Tickets by employee. Teams (DBA, Network, SRE Tier 2, SRE Tier 3, Other = reporting to other managers) come from Ardoq reporting lines, never from the roadmap deck: optional top-level `org_teams` `{"source", "as_of", "teams": [{"name", "manager", "manager_email", "members": [{"name", "email"}]}]}` (written by `org-collector`); when absent the renderer uses `${CLAUDE_PLUGIN_ROOT}/config/org-teams.json` and adds a "static snapshot" data gap. Assignees are matched by name or email (case and accents ignored); the manager counts in the team's headcount.

"Tickets added or removed from the sprint (day 2 onward)" (Sprint charts section 6) comes from optional `sprint.changes`, written by `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli sprint-changes <data.json>`: `[{"key", "url", "name", "status", "assignee", "action": "added"|"removed", "date": "yyyy-mm-dd" (America/New_York), "by", "other_sprint"}]`. Day 1 is the sprint start date; Sprint-field changes on later days are listed, and a ticket created straight into the sprint counts as added by its creator. Absent = section omitted; empty list = "no tickets added or removed". Each sprint subsection under "JIRA tickets" starts with "JIRA Tickets Link: Sprint <name>" (Jira issue navigator filtered to that sprint).

Header links: SharePoint Report Archive Link, Confluence Parent Page and JIRA ScrumBoard (`brand.JIRA_BOARD_URL`); the Sprint management tab starts with a JIRA ScrumBoard Link, then the "Sprint charts" and "JIRA tickets" sections.

Presentation rules built into the renderer: every table sorts by clicking a column header; dates print as mm/dd (ISO values are kept for sorting); IOSP/RM/COR keys in any text become Jira links; project cards and their sections collapse and expand (plus Collapse all / Expand all); both reports show the SharePoint location (`SHAREPOINT_REPORT_FOLDER_URL`, default the PMO AI Agent Factory / IO Project Assistant Reports folder) and the same footer (version, author, GitHub, sectigo.com).

Report style: management layout per the Sectigo brand 2026 (`${CLAUDE_PLUGIN_ROOT}/src/ioassistant/brand.py`, assets bundled in `${CLAUDE_PLUGIN_ROOT}/src/ioassistant/brand/`): summary tiles, projects at a glance, then per-project cards with the top 3 notes (rest collapsed), risks, action items and source links; sprint ticket list and data gaps are collapsed. Palette, fonts and logo come only from the bundled brand files.

The `--compact` build (written to `output/<RUN_ID>/upload/`) is for the connector upload: no embedded fonts or logo image, because file contents must be pasted into the upload call and cannot be reproduced reliably.

Render with `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli report output/<RUN_ID>/data.json`. Output: `output/<RUN_ID>/<RUN_ID>.html` (self-contained, all source links clickable).
