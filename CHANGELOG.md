# Changelog

Release notes for the IO Project Assistant plugin. Format: [Keep a Changelog](https://keepachangelog.com/).

Workflow: add entries under the in-development version at the top on `DEV` as you commit. When `DEV` is merged into `main` (PROD), rename
`[0.4.0] - in development` to the release date, bump `version` in `plugins/ioproject-assistant/.claude-plugin/plugin.json`,
tag the `main` commit `vX.Y.Z` and paste the section into the GitHub Release. DEV builds may use `X.Y.Z-dev.N`.

## [1.1.5] - 2026-11-14

### Added
- **Outlook status emails are listed in "Project sources"** (status report). When a run used the `<PROJECT> - Project Status (yyyy/mm/dd)` emails of a project (`links.email` in `data.json`), its card shows an "Outlook status emails" group with a link to each email, placed before the Jira strategic initiative and Planner groups. Projects without such emails get no group.

## [1.1.4] - 2026-11-13

### Added
- **Outlook project status emails are now a source** for every project, not only Rubrik. The Teams collector (skill `teams-standup-collection`, new step 2e) searches Outlook for subjects `<PROJECT NAME> - Project Status (yyyy/mm/dd)` (for example `NETWORK 2.0 - Project status (2026/11/13)` and `EOL OS Management - Project Status (2026/11/12)`), keeps those whose subject date is inside the analysis window, reads each in full and adds status, dates, owners, risks and asks to the project's notes, action items and risks (notes marked `status email <date>`). `NETWORK 2.0` is matched to "Network 2.0" and `EOL OS Management` to "EoL OS management" (the same project as the EoL chats); any other name becomes its own project and is reviewed by the Jira and Confluence collectors. `RUBRIK` emails stay in step 2b. A rating stated in an email is quoted in the notes but does not set the project `status` (the roadmap deck still comes first); conflicts with other sources go to `gaps`. New output field `sources.status_emails`.

## [1.1.3] - 2026-11-12

### Added
- **EoL OS management project chat is now collected** by the Teams collector (skill `teams-standup-collection`, step 2d), not only linked. The old chat is read for dates before 2026-11-12 and the new chat from 2026-11-12 (`TEAMS_EOL_CHAT_URL`, `TEAMS_EOL_CHAT_URL_NEW`, `TEAMS_EOL_CHAT_NEW_FROM` in `config/defaults.env`); a window that spans the date reads both. The new chat is also listed as "EoL OS management project chat 3" under "Project chats" in `config/project-resources.json`.

### Changed
- **EoL OS management has a fixed SharePoint source:** the folder "Upgrading Gentoo to Debian". It is shown under "SharePoint" in "Project sources" (status report) and "Key project resources" (leadership report), and the SharePoint collector reads it for EoL (`sharepoint-roadmap`, step 3b). `config/project-resources.json` accepts a new link kind `sharepoint`. The folder is removed from EoL's `exclude` list (added in 1.1.2); OS Lifecycle management still gets it from a run as before.

- **The upload copy now lists every active ticket** (it was capped at the first 20 per project, with a "left out of this copy" note), and every overdue ticket in "Jira task updates needed". The copy still leaves out the embedded fonts and the logo, so it is about 250 KB for a typical run (the full report is about 800 KB; the 1 MB inline limit of the connector upload is unchanged). `report.COMPACT_TICKET_CAP` is now `None`; set it to a number (20 gave about 170 KB) to cap tickets again if uploads fail on size.

## [1.1.2] - 2026-11-11

### Changed
- **EoL OS management no longer shows the Debian OS lifecycle management links** that a run found for it (Jira epic IOSP-806, Confluence "OS Lifecycle management" and "OS lifecycle mngmnt roadmap", SharePoint folder "Upgrading Gentoo to Debian"). `config/project-resources.json` entries have an optional `exclude` list of URLs that are dropped from what a run finds for that project, in the status report ("Project sources") and the leadership report ("Key project resources").

## [1.1.1] - 2026-11-10

### Changed
- **EoL OS management** has a second Teams project chat in its fixed resources (`config/project-resources.json`), shown with the first one under "Project chats".
- **RM tickets with status Success count as Done** in the status report (done counts, workload charts, burndown, overdue highlighting and the active-ticket lists). Other spaces are unchanged.

## [1.1.0] - 2026-11-09

### Added
- **Fixed project resources.** New `config/project-resources.json` and module `resources.py`: links that are added to a project on every run, matched by key words in the project name (whole words, case-insensitive). Shown in "Project sources" of the status report and in "Key project resources" of the leadership report, merged with what the run finds (a link with the same URL is shown once). Two new groups appear only for projects that have them: "Jira strategic initiative" and "Planner". Configured for **Network 2.0** (Jira epic IOSP-477, Confluence, Teams project chat, Planner), **EoL OS management** (strategic initiative SI-5, Confluence, Teams project chat) and **OS Lifecycle management** (Jira epic IOSP-806, Confluence, Planner; matches "OS lifecycle" and "Debian").
- **"What's next"** group in "Project updates (summary)" of each project in the status report, above "Risks": the project's action items with owner and due date (mm/dd). A project with no action items shows no group.

### Changed
- Status report, "Project sources" is laid out in two columns, in the order Jira epic(s), SharePoint, Confluence, Project chats; the labels match the leadership report (SharePoint, Confluence, Project chats).
- **Sprint management** covers two more Jira spaces, CITN (Corporate IT Network Team) and DBA. The board filter already included them, so no collection change was needed; the skill, agent and guide text now say so. The section "Employees without tickets assigned in sprint" is now "Employees without tickets assigned in sprint (IOSP, COR, CITN, DBA)".
- Leadership report header: the title is white and the word LEADERSHIP is underlined and highlighted (it was red).
- Leadership report: projects Paused by the proposal (or by the deck when the proposal gives no status) are listed last in the contents, at a glance and in the cards.

## [1.0.0] - 2026-11-07

### Added
- New pipeline **IO Projects Leadership Updates** (skill `run-leadership-updates`, agent `orchestrator-leadership`): regular update of the leadership project deck. It reads the main IO Project Assistant reports of the analysis period (default the last 7 days, `LEADERSHIP_PERIOD_DAYS`) and the I&O Project Roadmap deck (project slides 5-9, `LEADERSHIP_DECK_URL` / `LEADERSHIP_DECK_SLIDES`), and writes a report `IOProjectLeadershipUpdates_<yyyymmdd>_<hhmm>.html` (New York time) in the style of the main report: summary tiles, projects at a glance, contents rail, and the tabs "Project updates", "Sources" and "Data gaps". Each project card has the key changes of the period, then the deck's previous information on the left beside a proposal for the new statuses and text on the right (new and superseded bullets marked, with the reason), then the key project resources in two columns (Jira epics, Confluence, SharePoint, project chats, other links). At risk is orange, Off track red; the header title is red and the DEV tag off-white (`brand.banner` has optional `title_color` and `dev_color`; the other reports are unchanged). The deck is only read, never changed.
- The report is uploaded to the SharePoint report folder (next to the main report), a Confluence draft page `TEST: IO Projects Leadership Updates <yyyymmdd> <hhmm> (Draft)` is created under PMO AI Agent Factory > IO Project Assistant, and an unsent Outlook draft `IO Projects Leadership Updates <yyyymmdd> <hhmm>` is created (To `LEADERSHIP_EMAIL_TO`, default pmo@sectigo.com; CC the user). `continue from upload <RUN_ID>` resumes after a manual upload.
- The leadership run has its own **spending report** with the same rules as the main report: `usage.json` records model, tokens and seconds for every agent run (the orchestrator's own tokens are filled in by `run-leadership-updates` afterwards, which also refreshes the SharePoint copy), it is rendered by the existing `spend` command, uploaded next to the report (`<RUN_ID>_spending.html`) and linked from the Outlook draft and the Confluence page ("Spending report:" line, same place as in the main report's template). Its header reads "I&O PROJECTS LEADERSHIP UPDATES run - SPENDING" (the main report's spending header is unchanged).
- New commands `python -m ioassistant.cli leadership-collect <run folder> --from <ISO> --to <ISO>` (deterministic digest of the main reports per deck project, `reports.json`) and `leadership-report <data.json> [--compact]`; `email` and `confluence` build the leadership bodies when the run folder is a leadership run. Module `leadership.py`; project name matching between the deck and the main reports in `config/leadership-projects.json`.
- `collector-sharepoint` has a read-only **deck mode** (`sharepoint-roadmap` skill) that returns the deck's project slides with RAG letters, PM/TL and all text blocks, including Accomplishments (the status report's read mode still skips them).

### Changed
- `emaildraft.footer_block()` holds the footer shared by the Outlook draft and the Confluence page (output unchanged).
- The orchestrator agents follow one naming pattern: `orchestrator` is now `orchestrator-assistant-report` (launch it as `ioproject-assistant:orchestrator-assistant-report`) and the new `leadership-orchestrator` is `orchestrator-leadership`.
- The collector agents follow the same pattern: `confluence-collector`, `jira-collector`, `org-collector`, `sharepoint-collector` and `teams-collector` are now `collector-confluence`, `collector-jira`, `collector-org`, `collector-sharepoint` and `collector-teams` (launch them as `ioproject-assistant:collector-<name>`).

## [0.5.16] - 2026-11-05

### Changed
- `docs/PLUGIN_GUIDE.md` is updated to describe 0.5.15 (current version and changes table).

## [0.5.15] - 2026-11-04

### Changed
- The default "To" list of the Outlook draft (`REPORT_EMAIL_TO` in `config/defaults.env`, also in `.env.example`) now includes cody.bredendick@sectigo.com.
- The `confluence-release-log` skill states the real title of the parent page ("PMO AI Agent Factory: IO Project Assistant") and says that the page id and space are what identify the page.

## [0.5.14] - 2026-11-03

### Added
- New agent `release-log-publisher` (skill `confluence-release-log`) keeps a "RELEASE LOG" section at the end of the Confluence page PMO AI Agent Factory > IO Project Assistant (page 110166017). It lists the versions deployed to PROD, newest first, as a table with Version, Date and the list of changes, taken from the dated sections of `CHANGELOG.md` on `main` (sections still "in development" are never listed). The first run adds the section at the end of the page, later runs replace only that section; the rest of the page is untouched, an unchanged log is not published again, and the page body before the update is saved to `output/release-log/page_before.xhtml`. It is run by the maintainer from the repository after a release and is not part of `run-report`. New command `python -m ioassistant.cli release-log CHANGELOG.md [--page-body FILE] [--out FILE]` renders it.

## [0.5.13] - 2026-11-03

### Changed
- Daily Ops StandUp transcripts: for standups from 2026-10-27 (the "Daily Ops Standup (New)" meeting) the primary source is the meeting's own transcript, read through the calendar event's `meetingTranscriptUrl` for each day, not the "Daily Ops Standup_<yyyymmdd>" email. The emails are used only for standups before 2026-10-27. A day whose transcript cannot be read is a data gap and the chat is used for it. The old "organizer only, once per run" limit no longer applies to the new meeting (an attendee who is not the organizer can read it).

- The Sprint management "JIRA tickets" tables (current and past sprints) have the same columns as "Jira tickets for this project (active)": Ticket #, Ticket name, Status, Sprint, Responsible, Start, End, Related tickets (the old Due column is now End). Tickets that are not done and past their End date are highlighted with "overdue N d", as in the project tables. `sprint-tickets` now also reads Target start / Start date and the issue links from Jira (Start and Related tickets); links to tickets of any Jira project are listed, after the ones the Jira collector recorded. Ticket keys in this table are now links.

### Added
- The Outlook draft and the Confluence report page have a new line right after "Folder: IO Project Assistant Reports": "Confluence parent page: PMO AI Agent Factory", linking to the parent page (https://sectigo.atlassian.net/wiki/spaces/CO/pages/110166017/PMO+AI+Agent+Factory+IO+Project+Assistant).

## [0.5.12] - 2026-11-02

### Fixed
- The report no longer shows an ended sprint as the current one. Jira keeps a sprint "active" until someone closes it and the next sprint "future" until it is started, so on the Monday after a sprint ended the report still showed the old sprint (I&O 26.44 instead of I&O 26.45). The current sprint is now the one whose dates cover the report day: `sprint-tickets` makes the next sprint (even one not started yet) current when the sprint in `data.json` has ended, moves the ended sprint to the past sprints and adds a line to the Data gaps ("Current sprint: ... ended ... but is still active in Jira; the report uses ..."). When Jira has no dates for the next sprint, they are assumed from the previous one (same length, one week later) and the note says so. `sprint-changes` can read a sprint that has not started, and the Jira collector instructions state the same rule.

### Added
- "Sprint at a glance" opens with a link to the sprint's tickets in Jira, "JIRA Tickets Link: Active sprint I&O 26.45" (the same Jira ticket list the "JIRA tickets" section links to).

### Changed
- The Outlook draft now has a default "To" list (the PMO mailbox and the project leads) instead of no recipients. It comes from `REPORT_EMAIL_TO` in `config/defaults.env` (addresses separated by `;`; a `.env` in the working folder overrides it; empty means no "To"). CC is unchanged and the draft is still never sent.

## [0.5.11] - 2026-11-02

### Changed
- The Sprint charts section "Employees without tickets assigned in sprint" is now "Employees without tickets assigned in sprint (IOSP, COR)".

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
