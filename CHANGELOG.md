# Changelog

Release notes for the IO Project Assistant plugin. Format: [Keep a Changelog](https://keepachangelog.com/).

Workflow: add entries under `[Unreleased]` on `DEV` as you commit. When `DEV` is merged into `main` (PROD), rename
`[Unreleased]` to the version and date, bump `version` in `plugins/ioproject-assistant/.claude-plugin/plugin.json`,
tag the `main` commit `vX.Y.Z` and paste the section into the GitHub Release. DEV builds may use `X.Y.Z-dev.N`.

## [Unreleased]

### Added
- Contents rail on the status report, with a "Go to the top" link.
- Spending report totals row, footer links, sprint column and sprint subsections.
- Runs from the `DEV` branch use the `DEV_` file-name prefix and show a red "DEV:" before the report title.
- This changelog.

### Changed
- Report and spending file names use America/New_York time for `hhmm`.
- Middle dots are written as entities in the compact build.

## [0.3.3] - 2026-10-20
- Release 0.3.3 (see git history for details).

## [0.3.2] - 2026-10-20
- Release 0.3.2 (see git history for details).

## [0.3.1] - 2026-10-19
- Release 0.3.1 (see git history for details).
