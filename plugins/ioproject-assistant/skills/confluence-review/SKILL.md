---
name: confluence-review
description: Read Confluence project pages (https://sectigo.atlassian.net/wiki/) for discussed projects and extract status, dates, owners, recent edits.
---

# Confluence review

Base URL: `CONFLUENCE_BASE_URL` (https://sectigo.atlassian.net/wiki/, Confluence Cloud). Auth is the same as Jira: basic auth with `JIRA_EMAIL` and `JIRA_API_TOKEN` from `~/.ioassistant/secrets.env` (outside the repo), e.g. `curl -u "$JIRA_EMAIL:$JIRA_API_TOKEN"`; never print or persist them.

Read-only REST calls only: `/wiki/rest/api/content/search?cql=...` (e.g. `text ~ "<project>" AND lastmodified >= now("-1d")`) and `/wiki/rest/api/content/{id}?expand=body.storage,version`.

Example project page: https://sectigo.atlassian.net/wiki/spaces/CO/pages/94176950/Rubrik (space CO). Page URLs are `_links.base` + `_links.webui`.

For each discussed project with a Confluence page: title, URL, last editor, last modified, and the status/timeline/risk sections if present.

## Output JSON
```json
{"pages": [{"project": "", "title": "", "url": "", "last_modified": "", "last_editor": "", "summary": ""}], "gaps": []}
```
