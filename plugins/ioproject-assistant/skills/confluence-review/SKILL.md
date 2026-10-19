---
name: confluence-review
description: Read Confluence project pages (https://confluence.comodoca.net/) for discussed projects and extract status, dates, owners, recent edits.
---

# Confluence review

Base URL: `CONFLUENCE_BASE_URL`. The token is `CONFLUENCE_API_TOKEN` in `~/.ioassistant/secrets.env` (outside the repo). Send `Authorization: Bearer <token>`; never print or persist it.

Read-only REST calls only: `/rest/api/content/search?cql=...` (e.g. `text ~ "<project>" AND lastmodified >= now("-1d")`) and `/rest/api/content/{id}?expand=body.storage,version`.

For each discussed project with a Confluence page: title, URL, last editor, last modified, and the status/timeline/risk sections if present.

## Output JSON
```json
{"pages": [{"project": "", "title": "", "url": "", "last_modified": "", "last_editor": "", "summary": ""}], "gaps": []}
```
