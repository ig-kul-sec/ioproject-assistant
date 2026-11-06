# IO Project Assistant (Claude Code plugin)

Builds the daily I&O project status report. It reads the Daily Ops StandUp and Rubrik SyncUp Teams chats, Jira (IOSP, RM, COR), Confluence and the I&O Project Roadmap on SharePoint. It then produces a clickable HTML report and a spending report, uploads both to SharePoint, and prepares an **unsent** Outlook draft and a Confluence draft page.

## Install

```
/plugin marketplace add ig-kul-sec/ioproject-assistant
/plugin install ioproject-assistant@sectigo-io-tools
```

On Claude Code 2.1.275 or later this works in one step:

```
/plugin install ioproject-assistant --marketplace ig-kul-sec/ioproject-assistant
```

## Use

| Type this | What it does |
|---|---|
| `/ioproject-assistant:setup` | One-time setup and health check (Python, Jira/Confluence tokens, Microsoft 365, folder) |
| `/ioproject-assistant:run-report` | Builds today's report (default period: since Monday) |
| `/ioproject-assistant:run-report since 2026-10-12` | Same, for another period |
| `/ioproject-assistant:run-leadership-updates` | Leadership update: reads the main reports of the last 7 days and the I&O Project Roadmap deck, shows the deck's previous information beside a proposal for new statuses (HTML report, SharePoint, unsent Outlook draft to the PMO, Confluence draft page) |

Requirements: Python 3.10+ (no packages), the Microsoft 365 connector enabled in claude.ai, Jira and Confluence personal access tokens in `~/.ioassistant/secrets.env`.

Full step-by-step guide (sharing and day-to-day use): [docs/PLUGIN_GUIDE.md](../../docs/PLUGIN_GUIDE.md).

## Contents

- `agents/`: orchestrator-assistant-report, orchestrator-leadership, 4 collectors (Teams, Jira, Confluence, SharePoint), report builder, Outlook drafter, Confluence publisher
- `skills/`: the instructions each agent follows, plus `run-report`, `run-leadership-updates` and `setup`
- `src/ioassistant/`: report rendering (Python standard library only)
- `config/`: model prices and non-secret default settings
