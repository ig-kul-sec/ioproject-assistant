---
name: teams-standup-collection
description: 'Collect the Daily Ops StandUp chat and transcript plus the Rubrik Project SyncUp chat, transcript and "RUBRIK - Project Status" emails, for the analysis window (default: since Monday 00:00 America/New_York until now), via the Microsoft 365 connector and extract per-project updates.'
---

# Teams StandUp collection

Source: the Daily Ops StandUp chat (`TEAMS_STANDUP_CHAT_URL` in `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`, overridden by a `.env` in the working folder; thread id `19:meeting_NDAxMzEzOGEtZmUzYS00MTMxLTk3NTItODc1MGM1ZTBkZWQ2@thread.v2`).

1. Load the Microsoft 365 connector tools with ToolSearch (`mcp__claude_ai_Microsoft_365__*`). If only `authenticate` is available, stop and report "Teams: authentication required".
2. Fetch chat messages and the meeting transcript for the analysis window `{from, to}` given by the orchestrator. Default when none is given: `from` = Monday 00:00 of the current week (America/New_York), `to` = now. The window may cover several standups; collect them all and mark each note with the standup date.
   - **Messages:** do not rely on `read_resource` of `teams:///chats/{id}/messages`. It returns only the 50 most recently *updated* messages (ordered by last update, not send time) and has no next page. Use it only to learn the meeting/event ids.
   - Page through `chat_message_search` with `query: "*"`, `afterDateTime` / `beforeDateTime` set to the window, `limit: 25`, following `nextOffset` until `moreResults` is absent. The search covers every chat and channel and cannot filter by chat, so keep only results whose `chatUri` equals `teams:///chats/19%3Ameeting_NDAxMzEzOGEtZmUzYS00MTMxLTk3NTItODc1MGM1ZTBkZWQ2%40thread.v2/messages`. To cut alert-bot noise, repeat the search per participant with `sender` set (plus the meeting bot, whose messages show sender "Unknown" on direct reads); de-duplicate by message `id`.
   - Search `summary` is a short preview. For a message that matters (decisions, dates, owners) or whose preview ends in `...`, call `read_resource` on its `uri` for the full text.
   - **Transcript:** find the `Daily Ops Standup` event with `outlook_calendar_search`, read it, and pass its `meetingTranscriptUrl` to `read_resource` verbatim. Only the meeting organizer can read the transcript this way; the standup's organizer is not the signed-in user, so expect `NOT_FOUND` (HTTP 404, "Meeting properties are not found"). Do not retry. Record it in `gaps` ("Transcript unavailable: organizer-only access; chat and meeting-bot summaries used instead") and build the notes from chat only.
   - If paging stops early (error, rate limit), say in `gaps` which period was covered.
2b. **Second source: Rubrik Project SyncUp** (always collected in addition to the Daily Ops StandUp, never instead of it). Chat thread id `19:meeting_YjU0ZDdlMWEtNjc1Mi00Nzg4LTlhZjItNDBmMWEzNmExNzFl@thread.v2` (`TEAMS_RUBRIK_CHAT_URL` in `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`); filter search results on `chatUri` = `teams:///chats/19%3Ameeting_YjU0ZDdlMWEtNjc1Mi00Nzg4LTlhZjItNDBmMWEzNmExNzFl%40thread.v2/messages`.
   - Window: the same analysis window as step 2. Page `chat_message_search` as in step 2, searching per sender (Igor Kulyk, Calvin Cochran, Earle Long, Prajeet Singh Kahlon, SriChand Myla, Karl Witt, Gabriel Rovira) and on "Rubrik", filtered by `chatUri`, de-duplicated by message `id`. Read truncated previews in full.
   - Transcript: find the `Rubrik Project SyncUp` occurrence in the window with `outlook_calendar_search` and pass its `meetingTranscriptUrl` to `read_resource` verbatim. Igor Kulyk organizes this meeting, so it is readable only when he is the signed-in user; for anyone else expect `NOT_FOUND`, do not retry, and record the gap as for the standup transcript. The response's `meeting.startDateTime` is the series start, not the occurrence; take the date from the calendar event. The text is speech recognition, so names are often garbled (e.g. "Pavel", "Aurel"); match them to known participants and do not guess owners from garbled names.
   - Outlook status emails: `outlook_email_search` for subject `RUBRIK - Project Status` received in the window (newest first). Read each hit in full with `read_resource` on its uri. Use them for status, dates and owners; where an email conflicts with chat or transcript, keep both and add the conflict to `gaps`.
   - Report Rubrik as its own project (`name: "Rubrik DR backup"`, keys such as IOSP-471 and any RM/COR keys mentioned) in `projects`, and add the Rubrik source URLs under `sources`. Each note should say which source it came from (`standup chat`, `rubrik chat`, `rubrik transcript`, `status email`).
   - If any Rubrik source fails, record it in `gaps` and continue; a Rubrik failure never blocks the standup output, and vice versa.
3. Participants to expect: VP of I&O, I&O Director, I&O Managers, Incident Manager, Project Managers. Attribute action items to the speaker/owner named, not to the summarizer.
4. Identify projects discussed. Normalize names and capture JIRA keys (`IOSP-123`, `RM-45`, `COR-678`) mentioned.

## Output JSON

```json
{
  "window": {"from": "ISO", "to": "ISO"},
  "sources": {"chat_url": "...", "transcript_url": "...", "rubrik_chat_url": "...", "rubrik_transcript_url": "...", "rubrik_status_emails": [{"subject": "", "received": "ISO", "url": ""}]},
  "projects": [
    {"name": "", "jira_keys": [], "notes": [], "action_items": [{"text": "", "owner": "", "due": null}], "risks": []}
  ],
  "gaps": []
}
```
