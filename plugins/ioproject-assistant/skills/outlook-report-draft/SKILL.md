---
name: outlook-report-draft
description: Create an Outlook draft (never sent) with the SharePoint link to a finished IO Project Assistant report, CC the author, and the standard footer block.
---

# Outlook report draft

Input: `RUN_ID` (e.g. `IOProjectAssistantReport_20261017_1759`). Default: the newest folder in `output/` that has `<RUN_ID>.html`.

1. Build subject and body with `PYTHONPATH=src python -m ioassistant.cli email output/<RUN_ID>/data.json`. It writes `output/<RUN_ID>/upload/<RUN_ID>_email.html` (links to the report, the spending report and the SharePoint folder, then the footer block: `IO Project Assistant | Version | Author | GitHub` and `sectigo.com | Sectigo© 2026. All rights reserved.`). The subject is the run id with spaces: `IO Project Assistant Report 20261017 1759` (`ioassistant.emaildraft.subject_for`).
2. Load the connector tool with ToolSearch (`select:mcp__claude_ai_Microsoft_365__outlook_create_draft`). If it needs authentication, stop and report it.
3. `Read` the body file and call `outlook_create_draft` once: `subject`, `cc: ["igor.kulyk@sectigo.com"]`, no `to`, `body` = the file text exactly, `bodyType: "html"`.
4. **Never send.** Do not call `outlook_send_draft`, `outlook_send_mail`, `outlook_forward_mail` or any reply tool. Do not create a second draft if the first call succeeded.
5. **Attachment limit:** `outlook_create_draft` has no attachment parameter, so the report cannot be attached through the connector. Say so in the result: the draft carries the SharePoint link instead, and the user can attach the local file (`output/<RUN_ID>/<RUN_ID>.html`) by hand in Outlook. Never claim a file was attached.

Return the draft's `webLink` and a one-line note on the attachment limit.
