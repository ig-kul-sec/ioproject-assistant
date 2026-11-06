---
name: outlook-report-draft
description: Create an Outlook draft (never sent) with the SharePoint link to a finished IO Project Assistant report, CC the author, and the standard footer block.
---

# Outlook report draft

Input: `RUN_ID` (e.g. `IOProjectAssistantReport_20261017_1759`). Default: the newest folder in `output/` that has `<RUN_ID>.html`.

**Leadership updates variant:** when the `RUN_ID` starts with `IOProjectLeadershipUpdates` (or `DEV_IOProjectLeadershipUpdates`), the same steps apply with these differences. The body (written by the same `email` command, which picks the content from the run folder name) has the lead line `The latest IO Projects Leadership Updates are on SharePoint: period from yyyy/mm/dd till yyyy/mm/dd hh:mm`, then links to the report, the spending report, the SharePoint folder and the Confluence parent page, then the same footer block. The subject is `IO Projects Leadership Updates 20261105 1008` (the run id with spaces, `ioassistant.emaildraft.subject_for`). `to` comes from `LEADERSHIP_EMAIL_TO` in `defaults.env` (pmo@sectigo.com) instead of `REPORT_EMAIL_TO`; `cc` is still `["${user_config.cc_email}"]`. Never use the main report's recipient list for a leadership draft.

1. Build subject and body with `PYTHONPATH="${CLAUDE_PLUGIN_ROOT}/src" python -m ioassistant.cli email output/<RUN_ID>/data.json`. It writes `output/<RUN_ID>/upload/<RUN_ID>_email.html` (the lead line `The latest I&O project status report is on SharePoint: period from yyyy/mm/dd till yyyy/mm/dd hh:mm` with the run's analysis period, then links to the report, the spending report and the SharePoint folder, then the footer block: `IO Project Assistant | Version | Author | GitHub` and `sectigo.com | Sectigo© 2026. All rights reserved.`). The subject is the run id with spaces: `IO Project Assistant Report 20261017 1759` (`ioassistant.emaildraft.subject_for`).
2. Load the connector tool with ToolSearch (`select:mcp__claude_ai_Microsoft_365__outlook_create_draft`). If it needs authentication, stop and report it.
3. `Read` `${CLAUDE_PLUGIN_ROOT}/config/defaults.env` (a `.env` in the working folder overrides it) and take `REPORT_EMAIL_TO`: addresses separated by `;`, split into the `to` list (trim blanks). `Read` the body file and call `outlook_create_draft` once: `subject`, `to` (that list; leave `to` out only when `REPORT_EMAIL_TO` is empty or missing), `cc: ["${user_config.cc_email}"]` (the email the user gave when enabling the plugin; if it still reads as a placeholder, stop and ask them to set "Your work email" in `/config`), `body` = the file text exactly, `bodyType: "html"`.
4. **Never send.** Do not call `outlook_send_draft`, `outlook_send_mail`, `outlook_forward_mail` or any reply tool. Do not create a second draft if the first call succeeded.
5. **Attachment limit:** `outlook_create_draft` has no attachment parameter, so the report cannot be attached through the connector. Say so in the result: the draft carries the SharePoint link instead, and the user can attach the local file (`output/<RUN_ID>/<RUN_ID>.html`) by hand in Outlook. Never claim a file was attached.

Return the draft's `webLink` and a one-line note on the attachment limit.
