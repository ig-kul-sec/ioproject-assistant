---
name: sharepoint-roadmap
description: Read the PMO SharePoint folder and the I&O Project Roadmap PowerPoint for project statuses, and upload finished reports to the PMO folder.
---

# SharePoint + Roadmap

Locations come from `.env`: `SHAREPOINT_PMO_FOLDER_URL`, `SHAREPOINT_ROADMAP_URL` (site `IOProjectTeam`, file `Presentations/I&O Project Roadmap.pptx`), `SHAREPOINT_REPORT_FOLDER_URL` (`ITSM Freshservice/Archive/AI Test SharePoint Folder`).

## Read mode
1. Load Microsoft 365 connector tools via ToolSearch; if auth is required, report it as a gap.
2. Download/read the Roadmap deck; per discussed project extract status (RAG), milestones, dates, owner.
3. List the PMO folder; link files whose names match a discussed project.

## Upload mode
Upload only the files passed in (HTML report + spending report) to `SHAREPOINT_REPORT_FOLDER_URL`. Do not overwrite; on a name clash append `_2`. Return the web URL of each file.

## Output JSON
```json
{"roadmap": [{"project": "", "status": "", "start": null, "end": null, "owner": null, "notes": ""}],
 "files": [{"project": "", "name": "", "url": ""}], "uploaded": [{"name": "", "url": ""}], "gaps": []}
```
