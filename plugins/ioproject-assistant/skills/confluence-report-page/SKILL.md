---
name: confluence-report-page
description: 'Create a Confluence subpage under ITSM Freshservice (space CO) with the SharePoint links to the latest IO Project Assistant report (same content as the Outlook draft), titled "TEST: ... (Draft)".'
---

# Confluence report page

Base URL: `CONFLUENCE_BASE_URL` (https://confluence.comodoca.net/). The token is `CONFLUENCE_API_TOKEN` in `~/.ioassistant/secrets.env` (outside the repo). Send `Authorization: Bearer <token>`; load it in the shell command that makes the call; never print, log or persist it.

Input: `RUN_ID` (e.g. `IOProjectAssistantReport_20261017_1759`). Default: the newest folder in `output/` that has `data.json`.

1. Build the page body: `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli confluence output/<RUN_ID>/data.json`. It writes `output/<RUN_ID>/upload/<RUN_ID>_confluence.xhtml` (storage format) with the same content as the Outlook draft: the line "The latest I&O project status report is on SharePoint:", links to the report, the spending report and the SharePoint folder, then the footer block `IO Project Assistant | Version | Author | GitHub` and `sectigo.com | Sectigo© 2026. All rights reserved.`. Page title: `ioassistant.confluence.title_for(RUN_ID)`, e.g. `TEST: IO Project Assistant Report 20261017 1759 (Draft)`.
2. Find the parent: `GET /rest/api/content?spaceKey=CO&title=ITSM%20Freshservice&type=page`. It must return exactly one page (https://confluence.comodoca.net/display/CO/ITSM+Freshservice). Otherwise stop and report; never pick another page.
3. Check the title is free: `GET /rest/api/content?spaceKey=CO&title=<title>`. If a page exists, stop and return its URL; never overwrite or version an existing page.
4. Create it: build the JSON payload with a short Python script (title, `type: "page"`, `space: {key: "CO"}`, `ancestors: [{id: <parent id>}]`, `body.storage` = the xhtml file text, `representation: "storage"`), then `curl -X POST /rest/api/content` with that file as the data. If the body is rejected (400), report the error text and stop; do not retry in a loop.
5. Return the new page's URL (`_links.base` + `_links.webui`) and id.

Only this one create call writes to Confluence. No updates, deletes, labels or permission changes.
