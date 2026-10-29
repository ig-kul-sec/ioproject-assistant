# Changelog

Release notes for the IO Project Assistant plugin. Format: [Keep a Changelog](https://keepachangelog.com/).

Workflow: add entries under the in-development version at the top on `DEV` as you commit. When `DEV` is merged into `main` (PROD), rename
`[0.4.0] - in development` to the release date, bump `version` in `plugins/ioproject-assistant/.claude-plugin/plugin.json`,
tag the `main` commit `vX.Y.Z` and paste the section into the GitHub Release. DEV builds may use `X.Y.Z-dev.N`.

## [0.5.10] - 2026-10-30

### Changed
- The per-project subsection "Report sources" (the source counts) is removed; "Project sources" now sits directly before "Jira tickets for this project (active)", which is section 4.

## [0.5.9] - 2026-10-29

### Changed
- The per-project section "Jira tickets for this project" is now "Jira tickets for this project (active)" and lists only active tickets (not closed, done, resolved or complete), epic first, in the full report as well as the upload copy. A note under the table says how many closed or done tickets are not listed; the upload copy still shows at most the first 20 active tickets and says how many more are left out.

- Per-project sections are reorganised. "Project meeting chats", "Project SharePoint folder" and "Project Confluence page" are now one section "Project sources" (meeting chats, SharePoint folder, Confluence page and a link to the project's Jira epic, or epics when there are several), placed before "Report sources" (the former "Project sources": which sources the report used). Jira tickets is now section 5.
- "Jira tickets for this project (active)" opens sorted by sprint, ascending (numbers in the name compare by value, tickets without a sprint come last, epic first inside a sprint); the Sprint header shows the order and still toggles on click.

- "Tickets added or removed from the sprint (day 2 onward)" is now "Tickets added or removed from the sprint (during analyzed period)". The rule changed with the title: `sprint-changes` keeps every add or remove made inside the run's analysis window (start and end included, America/New_York), whatever the sprint day, and a ticket created straight into the sprint inside the window counts as added by its creator. The sentence above the table names the period ("During the analyzed period (10/27 - 10/29): N added, M removed."). Without a window in `data.json` the command falls back to the old day-2 rule.

### Added
- "Sprint burndown chart" is section 2 of the Sprint charts (the others move down by one; "Tickets added or removed from the sprint" is now section 7): open sprint tickets at the end of each working day against the ideal line, as a line chart with a data table and a one-line reading ("1 of 4 tickets open at 10/28, 1 ticket ahead of the ideal line"). A done ticket counts from its Jira resolution date, which `sprint-tickets` now reads (`resolved` on each sprint ticket); one without a date counts as done on the report day only, and the note says how many. Scope is the tickets in the sprint now: tickets added or removed during the sprint are not reflected. The chart ends on the report day (the end of the analysis window).
- Overdue tickets are highlighted. In "Jira tickets for this project (active)" a ticket whose End (Due) date is before the report day gets a coral row and an "overdue N d" tag on its End date (the tag says it in words, so colour is not the only signal). The report day is the end of the run's analysis window, so a report always shows what was overdue when it was built.
- "Jira task updates needed" gains a table "Tickets past their due date (update the date, or close the ticket)": the project's active tickets that are overdue, most overdue first (the upload copy shows the first 20 and says how many are left out), and "Existing tickets to change" now has a Due column. "No Jira updates identified." appears only when there is nothing to change, create or chase.

## [0.5.8] - 2026-10-29

### Changed
- The Outlook draft and the Confluence page now open with the analysis period: "The latest I&O project status report is on SharePoint: period from yyyy/mm/dd till yyyy/mm/dd hh:mm" (America/New_York, taken from the run's `window`; without a window the line stays as before).

### Added
- Postgres EDB migration: two more Teams chats are read every run and reported under the same project (`TEAMS_EDB_CHAT_URL_2`, `TEAMS_EDB_CHAT_URL_3` in `defaults.env` and `.env.example`). Notes say which chat they came from (`edb chat`, `edb chat 2`, `edb chat 3`), and a chat that cannot be read is a named data gap that does not block the others.

## [0.5.7] - 2026-10-28

### Fixed
- A blocked SharePoint upload no longer leaves a half-finished run. The main report is uploaded first (the spending report only if it succeeded), a denial is not retried, and the result gives the path for a manual upload. After a manual upload, `/ioproject-assistant:run-report continue from upload <RUN_ID>` creates the Outlook draft and the Confluence page without re-running the pipeline.
- The spending report on SharePoint never had the orchestrator's figures: it was uploaded before they were known, and only the local copy was updated. `run-report` step 3 now also rebuilds the compact `upload/` copy and, when the main report is on SharePoint, replaces only `<RUN_ID>_spending.html` there with the final figures (a narrow replace mode in the SharePoint skill; a denied refresh is not retried).
- A resume run (`continue from upload`) skipped the spending step, so its `orchestrator (resume)` row stayed at 0 tokens. `spend` has `--orchestrator-row` to fill that row without touching the first run's `orchestrator` row, and the skill now runs step 3 for resume runs.
- `spend` run with a bare `usage.json` from inside the run folder wrote `_spending.html` (empty run name). The path is now resolved first.
- A `~/.ioassistant/secrets.env` saved with a byte-order mark (Notepad can do this) made the first line unreadable: the first key was never loaded, and sourcing the file in the shell printed that line, token included, into the transcript. `sprint-changes` now reads the file as `utf-8-sig`, and `setup` strips a BOM after the user saves the file.

### Added
- `/ioproject-assistant:setup` asks once whether to approve the SharePoint report upload automatically. The default is no (each run asks); on a yes it adds `mcp__claude_ai_Microsoft_365__sharepoint_upload_file` to the user's own `permissions.allow` through the `update-config` skill, after explaining that the rule covers SharePoint uploads from any project. The plugin guide (B7, B8, B11) describes it, including the IT option through managed settings.
- `run-report` pre-flight checks folder access: it lists `output/` and reads the plugin's `config/defaults.env` before the run. When Claude's setting blocks reads outside the working directories it stops in seconds and tells the user to type `/add-dir <folder>`, instead of failing at the upload after a 30-minute run. The blocked-upload message gives the same hint.

## [0.5.6] - 2026-10-27

### Fixed
- The sprint ticket step failed with "data.json has no current sprint id" because the Jira agent did not return the Agile sprint ids, and runs needed a hand-edited `data.json`. The Jira skill and report schema now require `sprint.id` and `past_sprints[].id`, and `sprint-tickets` looks a missing id up on board 318 by sprint name before reading the tickets.

## [0.5.5] - 2026-10-27

### Fixed
- Jira tickets in the Rubrik project (and every IOSP ticket) showed no start/end dates: the collector read "Start date" and "Due date", but IOSP tickets keep their dates in "Target start" / "Target end". Both the collector and the sprint ticket list now read Target start/end first and fall back to Start date/Due date.
- The spending report showed 0 tokens and $0 for the orchestrator. `ioassistant.cli spend` now takes `--orchestrator-tokens` and `--orchestrator-seconds`, which write the orchestrator's own Agent result figures into `usage.json` before rendering; the run-report skill makes this step mandatory.

## [0.5.4] - 2026-10-27

### Fixed
- The report folder is now set explicitly (`SHAREPOINT_REPORT_FOLDER_URL` in `defaults.env` and `.env.example`) and the upload finds it by path, not by an exact-name search that returned nothing. A first PROD run on 2026-10-27 uploaded the spending report but the main report upload was blocked, so no Outlook draft or Confluence page was created. The Confluence parent (page 110166017) and SharePoint folder (`PMO AI Agent Factory/IO Project Assistant Reports`) are the 0.5.3 locations and are unchanged.
- "Existing tickets to change" suggested comments that the ticket description already contained (for example IOSP-1341 and IOSP-1342, created from the same standup). The Jira collector now also returns each ticket's `created` date and `description`, and the orchestrator skips comment suggestions the description already covers or that only repeat the standup a new ticket was created from.

## [0.5.3] - 2026-10-27

### Changed
- Report locations moved. Confluence report pages are now created under PMO AI Agent Factory > IO Project Assistant (space CO, page 110166017, https://sectigo.atlassian.net/wiki/spaces/CO/pages/110166017/PMO+AI+Agent+Factory+IO+Project+Assistant). Reports are uploaded to the SharePoint folder `PMO AI Agent Factory/IO Project Assistant Reports` on site IOProjectTeam. Header links, email draft and Confluence body use the new locations.

### Added
- Daily Ops StandUp: the new standup chat is read for standups from 2026-10-27 (`TEAMS_STANDUP_CHAT_URL_NEW`); earlier standups stay on the old chat.
- Postgres EDB migration: the project Teams chat (`TEAMS_EDB_CHAT_URL`) and the Jira epic IOSP-955 are read every run.

## [0.5.2] - 2026-10-26

### Fixed
- The sprint ticket lists could be incomplete: the Jira agent returned 30 of the 79 tickets in sprint I&O 26.44 (for example COR-12052 was missing), so the sprint charts and team workload undercounted. A new `sprint-tickets` command (`sprinttickets.py`) now reads every ticket of the current sprint and of each open past sprint from Jira, pages through all results and fails when the count does not match the sprint total. The orchestrator runs it after `data.json` is written; on failure it adds a "Sprint tickets: ..." gap and keeps the collector's list.

### Changed
- Guide: Jira Cloud connection and `DEV_` run prefix documented, release examples use 0.5.2, version history added (C8).

## [0.5.1] - 2026-10-26

### Changed
- Confluence moved to Confluence Cloud (https://sectigo.atlassian.net/wiki/, space CO). It uses the same `JIRA_EMAIL` + `JIRA_API_TOKEN` as Jira (basic auth), so `CONFLUENCE_API_TOKEN` is no longer needed. REST calls use `/wiki/rest/api/...`; the ITSM Freshservice parent page is https://sectigo.atlassian.net/wiki/spaces/CO/pages/94177160/ITSM+Freshservice.

## [0.5.0] - 2026-10-26

### Changed
- Jira moved to Jira Cloud (https://sectigo.atlassian.net/, same ticket keys). Authentication is now the Atlassian account email plus an API token (basic auth) instead of a Bearer personal access token: add `JIRA_EMAIL` next to `JIRA_API_TOKEN` in `~/.ioassistant/secrets.env` (the setup skill asks for both).
- The I&O Scrum board is board 318 (was 485); the report's JIRA ScrumBoard links, the sprint-changes section and the Jira collector instructions use it. The collector uses `/rest/api/2/search/jql` (the old search endpoint is gone on Cloud) and the Sprint field `customfield_10020`.

## [0.4.5] - 2026-10-26

### Fixed
- The report and spending report footer showed a stale version (0.3.2); it now shows the release version, and a test keeps it in step with `plugin.json`.

## [0.4.4] - 2026-10-26

### Changed
- Release of the 0.4.3 changes through the deployment pipeline. 0.4.3 reached `main` through pull request #1, so it has no tag or release.

## [0.4.3] - 2026-10-26

### Changed
- Plugin guide updated. The plugin itself is unchanged from 0.4.2.
- `output/` (local report runs) is no longer tracked in git and is listed in `.gitignore`.

## [0.4.2] - 2026-10-23

### Added
- Deployment pipeline "Deployment from DEV to PROD" (GitHub Actions): checks DEV, moves `main` (PROD) to it, tags the release and publishes a GitHub Release with the packaged plugin. Maintainer tooling only: the plugin itself is unchanged from 0.4.1.

## [0.4.1] - 2026-10-23

### Added
- "Tickets added or removed from the sprint (day 2 onward)" in Sprint charts: date, ticket, status, responsible and who made the change, from the Jira change history (new `sprint-changes` CLI command, run by the orchestrator; a ticket created straight into the sprint counts as added by its creator). Omitted, with a data gap, when Jira cannot be read.
- "JIRA Tickets Link: Sprint <name>" at the top of the current and past sprint subsections (Jira issue navigator for that sprint).
- Total rows in Tickets by status and Tickets by team, an Unassigned row in Tickets by team and Tickets by employee (the totals now equal all sprint tickets), and the team name next to each employee.

### Changed
- Sprint tickets and the status chart follow the workflow order: Backlog, To Do, In Progress, QA, On Hold, Unassigned, Done (other statuses after Done).
- "Engineers without tickets assigned in sprint" is now "Employees without tickets assigned in sprint", has a Manager column, no longer counts managers as employees, and comes before Tickets by employee.

## [0.4.0] - 2026-10-23

### Added
- Sprint charts (Sprint management tab): at-a-glance tiles, tickets by status (workflow order: Backlog, To Do, In Progress, QA, On Hold, Unassigned, Done), tickets by team, tickets by employee, and "Engineers without tickets assigned in sprint" (with the team manager).
- Teams (DBA, Network, SRE Tier 2, SRE Tier 3, Other) follow the reporting lines in Ardoq, not the roadmap deck: bundled Ardoq MCP server (`.mcp.json`), new `org-collector` agent that refreshes the roster, and a bundled snapshot `config/org-teams.json` used (and flagged as a data gap) when Ardoq is not signed in. The setup skill has an Ardoq sign-in step.
- Sprint management tab starts with a JIRA ScrumBoard link, then "Sprint charts" and "JIRA tickets" sections.
- Contents rail on the status report, with a "Go to the top" link.
- Tabs under the Collapse/Expand buttons: Projects, Operations, Sprint management and Data gaps (Sprint status and Data gaps moved into their tabs).
- Spending report totals row, footer links, sprint column and sprint subsections.
- Runs from the `DEV` branch use the `DEV_` file-name prefix and show a red "DEV:" before the report title.
- This changelog.

### Changed
- Report and spending file names use America/New_York time for `hhmm`.
- Middle dots are written as entities in the compact build.

## [0.3.2] - 2026-10-20
- Release 0.3.2 (see git history for details).

## [0.3.1] - 2026-10-19
- Release 0.3.1 (see git history for details).
