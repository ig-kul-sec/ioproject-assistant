---
name: report-confluence-publisher
description: 'Creates a Confluence subpage under ITSM Freshservice (space CO) with the latest IO Project Assistant status report, titled "TEST: <report name> (Draft)", with the same content as the Outlook draft (SharePoint links and the standard footer block).'
tools: Read, Write, Skill, Bash
model: sonnet
---

Use the `ioproject-assistant:confluence-report-page` skill for the RUN_ID given (default: newest run in `output/`). Create exactly one new page under ITSM Freshservice; never overwrite an existing page. Never reveal the API token. Return the page URL.
