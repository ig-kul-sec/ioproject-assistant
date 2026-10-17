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
    "name": "", "notes": [], "progress": "", "timeline": "", "dates": {"start": "", "end": ""},
    "action_items": [{"text": "", "owner": "", "due": ""}], "risks": [],
    "links": {"jira": [{"label": "", "url": ""}], "teams": [], "sharepoint": [], "confluence": []}
  }],
  "gaps": []
}
```

Render with `python -m ioassistant.cli report output/<RUN_ID>/data.json`. Output: `output/<RUN_ID>/<RUN_ID>.html` (self-contained, all source links clickable).
