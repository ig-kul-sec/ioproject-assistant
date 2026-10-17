---
name: teams-standup-collection
description: Collect the Daily Ops StandUp meeting transcript and chat messages from the last 24 hours via the Microsoft 365 connector and extract per-project updates.
---

# Teams StandUp collection

Source: the Daily Ops StandUp chat (`TEAMS_STANDUP_CHAT_URL` in `.env`, thread id `19:meeting_NDAxMzEzOGEtZmUzYS00MTMxLTk3NTItODc1MGM1ZTBkZWQ2@thread.v2`).

1. Load the Microsoft 365 connector tools with ToolSearch (`mcp__claude_ai_Microsoft_365__*`). If only `authenticate` is available, stop and report "Teams: authentication required".
2. Fetch chat messages and the meeting transcript with `createdDateTime >= now - 24h`.
3. Participants to expect: VP of I&O, I&O Director, I&O Managers, Incident Manager, Project Managers. Attribute action items to the speaker/owner named, not to the summarizer.
4. Identify projects discussed. Normalize names and capture JIRA keys (`IOSP-123`, `RM-45`, `COR-678`) mentioned.

## Output JSON

```json
{
  "window": {"from": "ISO", "to": "ISO"},
  "sources": {"chat_url": "...", "transcript_url": "..."},
  "projects": [
    {"name": "", "jira_keys": [], "notes": [], "action_items": [{"text": "", "owner": "", "due": null}], "risks": []}
  ],
  "gaps": []
}
```
