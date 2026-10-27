---
name: jira-project-review
description: Review JIRA tickets in the IOSP, RM and COR spaces for discussed projects and the active sprint (changes, comments, dates, assignees, statuses).
---

# JIRA project review

Instance: `JIRA_BASE_URL` (https://sectigo.atlassian.net/). The token is `JIRA_API_TOKEN` in `~/.ioassistant/secrets.env` (outside the repo). Jira Cloud uses basic auth: send `curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN"` (account email plus Atlassian API token; both in `secrets.env`). Load it in the shell command that makes the call; never print it, log it or write it to any project file.

Scrum board (backlog view, linked from the report header and under Sprint status): https://sectigo.atlassian.net/jira/software/c/projects/IOSP/boards/318/backlog (board id 318, "I&O Scrum", project IOSP). Read the active sprint from this board.

Spaces:
- **IOSP**: epics, tasks, weekly scrum boards. The active sprint feeds the SPRINT STATUS section.
- **RM**: release management tickets.
- **COR**: projects managed in COR.

For each discussed project (by key from the Teams collector, otherwise by epic/name search):
1. Epic + child tickets: key, summary, status, assignee, start date, due/end date, URL, `created` (YYYY-MM-DD), `description` (plain text of the ticket description, first 600 characters, null when empty) and `sprint` (the name of the active sprint the ticket is in, else its latest sprint, null if none; use the Agile "Sprint" field, whose id is `customfield_10020`, see `/rest/api/3/field`).
2. Changes and comments with `updated >= <window.from>` (the analysis window passed by the orchestrator; default since Monday 00:00 America/New_York) (author, time, short text).
3. Active IOSP sprint: name, start, end, duration in days, tickets as above. Also report `past_sprints` (a list, oldest first, each the same shape) with every other sprint on the board that has ended but is still not closed (state active, end date in the past); otherwise an empty list.

**Sprint tickets are complete, never condensed.** `sprint.tickets` (and each `past_sprints[].tickets`) lists every ticket in the sprint, whatever its project, status or assignee: fetch them with `sprint = <sprint id>` (`/rest/agile/1.0/sprint/{id}/issue` or `/rest/api/2/search/jql`), follow `nextPageToken` until the last page, and compare the count with the sprint's total before returning. Do not filter to project-relevant or notable tickets and do not merge ranges into one row: the report's totals and charts count these tickets. If a page fails, return what was read and add a gap with the missing count.

**Always-included epics** (reviewed every run, in addition to whatever the Teams collector reports; never replace the discussed-project list):
- **Rubrik DR backup: IOSP-471** (https://sectigo.atlassian.net/browse/IOSP-471). Fetch the epic itself (summary, status, description/objectives, assignee, dates) and all child issues (`"Epic Link" = IOSP-471`, plus issue links to RM and COR tickets such as RM-1658, RM-1660). Apply steps 1 and 2 to it. Report it as the project "Rubrik DR backup".
- **Postgres EDB migration: IOSP-955** (https://sectigo.atlassian.net/browse/IOSP-955). Fetch the epic itself (summary, status, description/objectives, assignee, dates), its comments and recent changes since the start of the window, and all child issues (`"Epic Link" = IOSP-955`, plus issue links to RM and COR tickets). Apply steps 1 and 2 to it. Report it under the same project name the Teams collector uses for the EDB chat (see step 2c of `teams-standup-collection`), so the chat and Jira data merge into one project.

Return every project's tickets as the structured `tickets` list in the output JSON: the epic itself (`epic: true`) plus all child tickets, including closed ones, with `start`/`end` from the start-date and due-date fields (null when empty), the assignee's display name, and `related` from issue links and linked RM/COR tickets (key + browse URL).

**Daily Ops items** (when the orchestrator passes the Teams collector's `non_project` list): for each item, find related tickets in IOSP, RM and COR. First fetch every key the item already lists. Then run a narrow text search on the item's distinctive terms, e.g. `project in (IOSP, RM, COR) AND text ~ "\"DNS connector\"" AND updated >= -30d ORDER BY updated DESC`, and keep at most 3 matches. Keep a match only if its summary clearly refers to the same system or incident; never pad with loosely related tickets. Return each item's `title` with `tickets` (`key`, `url`, `status`, `summary`); an item with no confident match gets an empty list.

Use read-only REST calls (`/rest/api/2/search/jql` (the old `/rest/api/2/search` is removed on Cloud; it pages with `nextPageToken`, not `startAt`), `/rest/agile/1.0/board/{id}/sprint`). If the API is unreachable, fall back to the connector/browser if available, else record a gap.

## Output JSON

```json
{
  "sprint": {"name": "", "start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "tickets": [
    {"key": "", "url": "", "summary": "", "status": "", "assignee": "", "due": null}]},
  "past_sprints": [],
  "projects": [{"name": "", "changes": [{"key": "", "who": "", "when": "", "text": ""}],
    "tickets": [{"key": "", "url": "", "name": "", "status": "", "sprint": null, "assignee": "", "start": null, "end": null,
                 "created": "YYYY-MM-DD", "description": null, "epic": false, "related": [{"key": "", "url": ""}]}]}],
  "daily_ops": [{"title": "", "tickets": [{"key": "", "url": "", "status": "", "summary": ""}]}],
  "gaps": []
}
```
