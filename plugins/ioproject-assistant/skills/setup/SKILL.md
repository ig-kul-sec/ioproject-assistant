---
name: setup
description: One-time setup and health check for the IO Project Assistant plugin (Python, Jira and Confluence tokens, Microsoft 365 connector, report folder, CC email). Use when the user installs the plugin, asks to set it up, or a report run says something is missing.
---

# IO Project Assistant setup

The user is probably not technical. Do one step at a time, explain each in one or two plain sentences, and finish with a checklist (✅ / ❌ and what to do). Never ask the user to paste a token into the chat, and never print, echo or log a token.

## 1. Python

Run `python --version`. Python 3.10 or newer passes. Otherwise tell the user:
- **Windows:** open the Microsoft Store, search "Python 3.13", click **Get**, then close and reopen Claude.
- **Mac:** download the installer from https://www.python.org/downloads/ and run it, then reopen Claude.

No extra packages are needed.

## 2. Atlassian token (Jira and Confluence)

The file is `~/.ioassistant/secrets.env` (in the user's home folder, outside any project).

1. If it does not exist, create it (never overwrite an existing one):
   ```bash
   mkdir -p "$HOME/.ioassistant" && [ -e "$HOME/.ioassistant/secrets.env" ] || printf 'JIRA_EMAIL=paste_your_atlassian_email_here\nJIRA_API_TOKEN=paste_your_jira_token_here\n' > "$HOME/.ioassistant/secrets.env"
   ```
2. Explain how to create the token (one Atlassian Cloud API token covers both Jira and Confluence):
   - **Jira:** open https://id.atlassian.com/manage-profile/security/api-tokens → **Create API token** → name it "IO Project Assistant" → **Create** → copy the token. Also put the email you sign in to https://sectigo.atlassian.net/ with in `JIRA_EMAIL`.
   - **Confluence:** the same email and token work for https://sectigo.atlassian.net/wiki/; nothing more to create.
3. Open the file for them: Windows `notepad "$HOME/.ioassistant/secrets.env"`; Mac `open -e "$HOME/.ioassistant/secrets.env"`. They replace each `paste_..._here` with the email or token (no spaces, no quotes), save and close Notepad, then tell you "done".
4. Test without showing the tokens; print only the HTTP status:
   ```bash
   set -a; . "$HOME/.ioassistant/secrets.env"; set +a
   curl -s -o /dev/null -w "Jira %{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" https://sectigo.atlassian.net/rest/api/3/myself
   curl -s -o /dev/null -w "Confluence %{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" https://sectigo.atlassian.net/wiki/rest/api/space/CO
   ```
   200 = working. 401/403 = the token is wrong or expired (make a new one). No answer / 000 = not on the company network or VPN.

## 3. Microsoft 365 connector (Teams, Outlook, SharePoint)

Load `mcp__claude_ai_Microsoft_365__get_me` with ToolSearch and call it.
- Works: show the signed-in name and email and confirm it is them.
- Not found, or only `authenticate` is available: tell the user to open https://claude.ai → **Settings** → **Connectors** → **Microsoft 365** → **Connect**, sign in with their Sectigo account and accept, then restart Claude. If Microsoft 365 is not in the list, their Claude admin has to enable it for the organization. Claude must be signed in with the company claude.ai account (`/login`), not an API key.

## 3b. Ardoq (team reporting lines)

The sprint workload chart groups tickets by team using the reporting lines in Ardoq. The plugin bundles the Ardoq server, so ask the user to type `/mcp`, pick **ardoq** and sign in with their Sectigo account once. If they skip it, the report still works: it uses the bundled roster snapshot (`config/org-teams.json`) and lists a data gap saying Ardoq was not connected. An Ardoq account with access to the Entra Users workspace is needed for live data.

## 4. Report folder

Reports are written to `output/` inside the folder Claude was opened in. Show the current folder (`pwd`). If it is the home folder, the Desktop or a code project, suggest a dedicated folder such as `Documents/IO Reports`, offer to create it, and explain they should choose that folder each time they start Claude for reports.

On Windows the full folder path must be under 140 characters (check with `pwd -W | wc -c`): report files add about 110 more, and Windows refuses paths over 260. If it is longer, suggest a shorter folder such as `C:\IOReports`.

## 5. CC email

The Outlook draft is CC'd to: `${user_config.cc_email}`. If that is wrong or looks like a placeholder, tell them to type `/config`, find **ioproject-assistant → Your work email**, and change it.

## 6. Access the report needs (cannot be checked from here)

Tell the user the run also needs read access to the Daily Ops StandUp and Rubrik Project SyncUp Teams chats, the I&O Project Roadmap on SharePoint, and write access to the "IO Project Assistant Reports" SharePoint folder and the Confluence space CO. Missing access does not stop the run; it shows up as a data gap in the report.

## 6b. SharePoint upload without a prompt (optional, ask once)

Each run asks the user to approve the SharePoint upload. Ask once whether they want to skip that prompt: "Each report run asks you to approve the upload to the SharePoint reports folder. Do you want me to allow it automatically from now on? The setting applies to SharePoint uploads from any Claude project on this computer, not only to the report folder. You can remove it later with `/permissions`." Default is **no**: only act on an explicit yes, and say that no is fine.

- **Yes:** use the `update-config` skill to add `mcp__claude_ai_Microsoft_365__sharepoint_upload_file` to `permissions.allow` in the user's own settings (user scope, not the project). Do not touch any other setting, and never add it without the yes.
- **No, or no answer:** change nothing. The run asks for approval each time.

Report it in the checklist as "SharePoint upload approval: automatic" or "asked each run".

Finish with the checklist and, if everything is ✅, say: "You're ready. Type `/ioproject-assistant:run-report` to make today's report."
