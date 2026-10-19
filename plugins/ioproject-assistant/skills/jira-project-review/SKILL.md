---
name: jira-project-review
description: Review JIRA tickets in the IOSP, RM and COR spaces for discussed projects and the active sprint (changes, comments, dates, assignees, statuses).
---

# JIRA project review

Instance: `JIRA_BASE_URL` (https://projects.sectigo.net/). The token is `JIRA_API_TOKEN` in `~/.ioassistant/secrets.env` (outside the repo). Send it as `Authorization: Bearer <token>` (personal access token). Load it in the shell command that makes the call; never print it, log it or write it to any project file.

Scrum board (planning view, linked from the report header and under Sprint status): https://projects.sectigo.net/secure/RapidBoard.jspa?rapidView=485&projectKey=IOSP&view=planning.nodetail&issueLimit=100 (board id 485, project IOSP). Read the active sprint from this board.

Spaces:
- **IOSP**: epics, tasks, weekly scrum boards. The active sprint feeds the SPRINT STATUS section.
- **RM**: release management tickets.
- **COR**: projects managed in COR.

For each discussed project (by key from the Teams collector, otherwise by epic/name search):
1. Epic + child tickets: key, summary, status, assignee, start date, due/end date, URL.
2. Changes and comments with `updated >= <window.from>` (the analysis window passed by the orchestrator; default since Monday 00:00 America/New_York) (author, time, short text).
3. Active IOSP sprint: name, start, end, duration in days, tickets as above.

**Always-included epics** (reviewed every run, in addition to whatever the Teams collector reports; never replace the discussed-project list):
- **Rubrik DR backup: IOSP-471** (https://projects.sectigo.net/browse/IOSP-471). Fetch the epic itself (summary, status, description/objectives, assignee, dates) and all child issues (`"Epic Link" = IOSP-471`, plus issue links to RM and COR tickets such as RM-1658, RM-1660). Apply steps 1 and 2 to it. Report it as the project "Rubrik DR backup".

Return every project's tickets as the structured `tickets` list in the output JSON: the epic itself (`epic: true`) plus all child tickets, including closed ones, with `start`/`end` from the start-date and due-date fields (null when empty), the assignee's display name, and `related` from issue links and linked RM/COR tickets (key + browse URL).

Use read-only REST calls (`/rest/api/2/search`, `/rest/agile/1.0/board/{id}/sprint`). If the API is unreachable, fall back to the connector/browser if available, else record a gap.

## Output JSON

```json
{
  "sprint": {"name": "", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "tickets": [
    {"key": "", "url": "", "summary": "", "status": "", "assignee": "", "due": null}]},
  "projects": [{"name": "", "changes": [{"key": "", "who": "", "when": "", "text": ""}],
    "tickets": [{"key": "", "url": "", "name": "", "status": "", "assignee": "", "start": null, "end": null,
                 "epic": false, "related": [{"key": "", "url": ""}]}]}],
  "gaps": []
}
```
