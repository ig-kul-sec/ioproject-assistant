---
name: sharepoint-roadmap
description: Read the PMO SharePoint folder and the I&O Project Roadmap PowerPoint for project statuses, and upload finished reports to the PMO folder.
---

# SharePoint + Roadmap

Locations come from `${CLAUDE_PLUGIN_ROOT}/config/defaults.env` (a `.env` in the working folder overrides it): `SHAREPOINT_PMO_FOLDER_URL`, `SHAREPOINT_ROADMAP_URL` (site `IOProjectTeam`, file `Presentations/I&O Project Roadmap.pptx`), `SHAREPOINT_REPORT_FOLDER_URL` (`PMO AI Agent Factory/IO Project Assistant Reports`).

## Read mode
1. Load Microsoft 365 connector tools via ToolSearch; if auth is required, report it as a gap.
2. Download/read the Roadmap deck; per discussed project extract status (RAG), milestones, dates, owner, Project Manager and Technical Lead. **Use only the "Project review" slides.** Skip every other part of the deck (Other updates, Appendix, and so on). **Skip the "Accomplishments" content entirely**: do not use it for the summary, the status or the planning (dates, milestones, next steps). If a Project review slide mixes in an Accomplishments block, leave that block out.
3. List the PMO folder; link files whose names match a discussed project.

## Upload mode
Upload only the files passed in (HTML report + spending report) to `SHAREPOINT_REPORT_FOLDER_URL`. Do not overwrite; on a name clash append `_2`. Return the web URL of each file.

**Method: direct upload through the Microsoft 365 connector** (`sharepoint_upload_file`; do not go through OneDrive sync or copy tools). The tool takes the file contents inline (max 1 MB, no file-path option, no chunking), so upload the compact builds the orchestrator made in `output/<RUN_ID>/upload/` (`PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli report|spend --compact`: no embedded fonts and no logo image, LF line endings, about 56 KB and 3 KB). Never strip anything yourself and never retype content from memory.
1. Find the report folder with `sharepoint_folder_search` (`IO Project Assistant Reports`) or `read_resource`, to get `driveId` and `parentItemId`.
2. For each file: `Read` it, then call `sharepoint_upload_file` with `content` set to the file text, byte-for-byte, `filename` the file name, `conflictBehavior: "rename"` is NOT allowed; use the default `fail`, and on a name clash retry once with `filename` suffixed `_2` before the extension. Pass `expectedBytes` = the byte count the orchestrator gives you for that file (the tool rejects the write if the received length differs; if it does, re-read and retry once, then report the failure).
   **Replace mode:** only when the caller says the user asked to update the existing files, set `conflictBehavior: "replace"` for exactly those files (same names, no `_2`). Without that instruction, never overwrite.
3. Return the `webUrl` of each uploaded file. If a file fails, say which and why; do not retry in a loop.

## Output JSON
```json
{"roadmap": [{"project": "", "status": "", "start": null, "end": null, "owner": null, "project_manager": null, "technical_lead": null, "notes": ""}],
 "files": [{"project": "", "name": "", "url": ""}], "uploaded": [{"name": "", "url": ""}], "gaps": []}
```
