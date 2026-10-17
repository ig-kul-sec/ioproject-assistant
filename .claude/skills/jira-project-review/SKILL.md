---
name: jira-project-review
description: Review JIRA tickets in the IOSP, RM and COR spaces for discussed projects and the active sprint (changes, comments, dates, assignees, statuses).
---

# JIRA project review

Instance: `JIRA_BASE_URL` (https://projects.sectigo.net/). The token is `JIRA_API_TOKEN` in `~/.ioassistant/secrets.env` (outside the repo). Send it as `Authorization: Bearer <token>` (personal access token). Load it in the shell command that makes the call; never print it, log it or write it to any project file.

Spaces:
- **IOSP**: epics, tasks, weekly scrum boards. The active sprint feeds the SPRINT STATUS section.
- **RM**: release management tickets.
- **COR**: projects managed in COR.

For each discussed project (by key from the Teams collector, otherwise by epic/name search):
1. Epic + child tickets: key, summary, status, assignee, start date, due/end date, URL.
2. Changes and comments with `updated >= -24h` (author, time, short text).
3. Active IOSP sprint: name, start, end, duration in days, tickets as above.

Use read-only REST calls (`/rest/api/2/search`, `/rest/agile/1.0/board/{id}/sprint`). If the API is unreachable, fall back to the connector/browser if available, else record a gap.

## Output JSON

```json
{
  "sprint": {"name": "", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "tickets": [
    {"key": "", "url": "", "summary": "", "status": "", "assignee": "", "due": null}]},
  "projects": [{"name": "", "tickets": [], "changes_24h": [{"key": "", "who": "", "when": "", "text": ""}]}],
  "gaps": []
}
```
