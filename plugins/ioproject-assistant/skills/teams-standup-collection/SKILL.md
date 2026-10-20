---
name: teams-standup-collection
description: 'Collect the Daily Ops StandUp chat and transcripts (from the "Daily Ops Standup_<yyyymmdd>" transcript emails) plus the Rubrik Project SyncUp chat, transcript and "RUBRIK - Project Status" emails, for the analysis window (default: since Monday 00:00 America/New_York until now), via the Microsoft 365 connector and extract per-project updates.'
---

# Teams StandUp collection

Source: the Daily Ops StandUp chat (`TEAMS_STANDUP_CHAT_URL` in `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`, overridden by a `.env` in the working folder; thread id `19:meeting_NDAxMzEzOGEtZmUzYS00MTMxLTk3NTItODc1MGM1ZTBkZWQ2@thread.v2`).

1. Load the Microsoft 365 connector tools with ToolSearch (`mcp__claude_ai_Microsoft_365__*`). If only `authenticate` is available, stop and report "Teams: authentication required".
2. Fetch chat messages and the meeting transcript for the analysis window `{from, to}` given by the orchestrator. Default when none is given: `from` = Monday 00:00 of the current week (America/New_York), `to` = now. The window may cover several standups; collect them all and mark each note with the standup date.
   - **Messages:** do not rely on `read_resource` of `teams:///chats/{id}/messages`. It returns only the 50 most recently *updated* messages (ordered by last update, not send time) and has no next page. Use it only to learn the meeting/event ids.
   - Page through `chat_message_search` with `query: "*"`, `afterDateTime` / `beforeDateTime` set to the window, `limit: 25`, following `nextOffset` until `moreResults` is absent. The search covers every chat and channel and cannot filter by chat, so keep only results whose `chatUri` equals `teams:///chats/19%3Ameeting_NDAxMzEzOGEtZmUzYS00MTMxLTk3NTItODc1MGM1ZTBkZWQ2%40thread.v2/messages`. To cut alert-bot noise, repeat the search per participant with `sender` set (plus the meeting bot, whose messages show sender "Unknown" on direct reads); de-duplicate by message `id`.
   - Search `summary` is a short preview. For a message that matters (decisions, dates, owners) or whose preview ends in `...`, call `read_resource` on its `uri` for the full text.
   - **Transcript (primary source: Outlook transcript emails).** Each standup's transcript is emailed as a OneDrive link with subject `Daily Ops Standup_<yyyymmdd>` (e.g. `Daily Ops Standup_20261019`, body links `Daily Ops Standup_20261019.docx`).
     1. `outlook_email_search` with `query: "\"Daily Ops Standup_\""` and `afterDateTime` = window `from`; page through `nextOffset`. Keep subjects matching `Daily Ops Standup_<yyyymmdd>` whose date is inside the window; the same email can appear twice (Inbox and Sent Items), so de-duplicate by `internetMessageId`, then by date.
     2. `read_resource` the email and take the linked file name (`Daily Ops Standup_<yyyymmdd>.docx`) from the body.
     3. Find the file: `read_resource` on `drive:///users/me`, take the `OneDrive` drive URI, list its `Attachments` folder (`file:///<driveId>/Attachments`) and match the file name. If it is not there (the link points to someone else's OneDrive), use `sharepoint_search` for the exact file name; the search index can lag by hours for new files.
     4. `read_resource` the file's `file:///` URI with `startPage: 1`, following the `[truncated: pages … re-call with startPage=N]` footer until the last page. The text is `Speaker  m:ss  text`; it is speech recognition, so match garbled names to known participants.
     Use the transcript as the main record of what was said; mark those notes `standup transcript` with the standup date. For a standup in the window with no transcript email, or a file that cannot be read, add a gap naming the date ("Standup transcript <date>: no transcript email" or "…: file not readable") and use the chat for that day.
   - **Transcript (fallback, organizer only):** only for a standup date with no transcript email, the calendar event's `meetingTranscriptUrl` may be passed to `read_resource` verbatim. It works only for the meeting organizer (Shane Knable); for anyone else it returns `NOT_FOUND` ("Meeting properties are not found"). Try it at most once per run, never retry, and do not add a separate gap for it.
   - If paging stops early (error, rate limit), say in `gaps` which period was covered.
   - **Link labels must be unique and say what the link is.** Format: `<meeting> <yyyy-mm-dd> · <kind> (<hh:mm> UTC)`, e.g. `Standup 2026-10-14 · midpoint recap (13:15 UTC)`, `Standup 2026-10-14 · closing recap (13:24 UTC)`, `Standup 2026-10-19 · transcript`, `Rubrik SyncUp 2026-10-14 · transcript`. The meeting assistant (Facilitator) usually posts two recaps per meeting, a midpoint recap ("We're at the midpoint…") and a closing recap ("About N minutes remain…"); name them that way, otherwise `recap`. Never give two different messages the same label, and list each message URL once.
2b. **Second source: Rubrik Project SyncUp** (always collected in addition to the Daily Ops StandUp, never instead of it). Chat thread id `19:meeting_YjU0ZDdlMWEtNjc1Mi00Nzg4LTlhZjItNDBmMWEzNmExNzFl@thread.v2` (`TEAMS_RUBRIK_CHAT_URL` in `${CLAUDE_PLUGIN_ROOT}/config/defaults.env`); filter search results on `chatUri` = `teams:///chats/19%3Ameeting_YjU0ZDdlMWEtNjc1Mi00Nzg4LTlhZjItNDBmMWEzNmExNzFl%40thread.v2/messages`.
   - Window: the same analysis window as step 2. Page `chat_message_search` as in step 2, searching per sender (Igor Kulyk, Calvin Cochran, Earle Long, Prajeet Singh Kahlon, SriChand Myla, Karl Witt, Gabriel Rovira) and on "Rubrik", filtered by `chatUri`, de-duplicated by message `id`. Read truncated previews in full.
   - Transcript: find the `Rubrik Project SyncUp` occurrence in the window with `outlook_calendar_search` and pass its `meetingTranscriptUrl` to `read_resource` verbatim. Igor Kulyk organizes this meeting, so it is readable only when he is the signed-in user; for anyone else expect `NOT_FOUND`, do not retry, and record the gap as for the standup transcript. The response's `meeting.startDateTime` is the series start, not the occurrence; take the date from the calendar event. The text is speech recognition, so names are often garbled (e.g. "Pavel", "Aurel"); match them to known participants and do not guess owners from garbled names.
   - Outlook status emails: `outlook_email_search` for subject `RUBRIK - Project Status` received in the window (newest first). Read each hit in full with `read_resource` on its uri. Use them for status, dates and owners; where an email conflicts with chat or transcript, keep both and add the conflict to `gaps`.
   - Report Rubrik as its own project (`name: "Rubrik DR backup"`, keys such as IOSP-471 and any RM/COR keys mentioned) in `projects`, and add the Rubrik source URLs under `sources`. Each note should say which source it came from (`standup transcript`, `standup chat`, `rubrik chat`, `rubrik transcript`, `status email`).
   - If any Rubrik source fails, record it in `gaps` and continue; a Rubrik failure never blocks the standup output, and vice versa.
3. Participants to expect: VP of I&O, I&O Director, I&O Managers, Incident Manager, Project Managers. Attribute action items to the speaker/owner named, not to the summarizer.
4. Identify projects discussed. Normalize names and capture JIRA keys (`IOSP-123`, `RM-45`, `COR-678`) mentioned.
5. **Non-project updates (Daily Ops StandUp only).** The standup also covers operations that belong to no project: system health, incidents (e.g. OCSP, DNS connector, issuance), problems and RCAs, blockers, changes and maintenance windows. Collect these from the standup transcripts, recaps and chat messages into `non_project`, never into `projects` (a project item stays under its project). Use one row per topic: `date` is the latest standup date it was discussed, `status` its latest state or next step, and `detail` a short history if it changed across days. Classify `type` as Incident, Problem, Issue, Change, Maintenance or Other (definitions in the `ioproject-assistant:report-generation` skill). Set `reported_by` to the person who gave the latest update on that item. Take it from the transcript speaker, the chat message author, or a person the recap names as giving the update ("Calvin reported…"). Never use the Facilitator bot or a summarizer; use null if no one is named. Fill `owner` only when a source names one, add any Jira keys mentioned to `tickets`, and set `source` to the latest standup link where it was discussed (unique label as above). Routine "all healthy" notes become one Other row per standup date only if nothing else was reported that day.

## Output JSON

```json
{
  "window": {"from": "ISO", "to": "ISO"},
  "sources": {"chat_url": "...", "transcript_url": "...", "standup_transcripts": [{"date": "YYYY-MM-DD", "subject": "", "email_url": "", "file": "", "file_url": ""}], "rubrik_chat_url": "...", "rubrik_transcript_url": "...", "rubrik_status_emails": [{"subject": "", "received": "ISO", "url": ""}]},
  "projects": [
    {"name": "", "jira_keys": [], "notes": [], "action_items": [{"text": "", "owner": "", "due": null}], "risks": []}
  ],
  "non_project": [
    {"date": "YYYY-MM-DD", "type": "Incident", "title": "", "detail": "", "status": "", "reported_by": null, "owner": null, "tickets": [], "source": {"label": "", "url": ""}}
  ],
  "gaps": []
}
```
