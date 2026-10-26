# Changelog

Release notes for the IO Project Assistant plugin. Format: [Keep a Changelog](https://keepachangelog.com/).

Workflow: add entries under the in-development version at the top on `DEV` as you commit. When `DEV` is merged into `main` (PROD), rename
`[0.4.0] - in development` to the release date, bump `version` in `plugins/ioproject-assistant/.claude-plugin/plugin.json`,
tag the `main` commit `vX.Y.Z` and paste the section into the GitHub Release. DEV builds may use `X.Y.Z-dev.N`.

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
