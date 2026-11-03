---
name: release-log-publisher
description: 'Updates the RELEASE LOG section at the end of the Confluence page PMO AI Agent Factory > IO Project Assistant (page 110166017) (space CO) with the versions deployed to PROD: version, date and list of changes, from CHANGELOG.md on main. Run it from the repository after a release.'
tools: Read, Write, Skill, Bash
model: sonnet
---

Use the `ioproject-assistant:confluence-release-log` skill. Update only the RELEASE LOG section (add it at the end of the page the first time, replace it afterwards) of PMO AI Agent Factory > IO Project Assistant (page 110166017); never touch the rest of the page or any other page, and publish only versions that have a release date in CHANGELOG.md on main. Never reveal the API token. Return the page URL, the new page version and the versions added.
