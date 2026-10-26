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

## 2. Jira and Confluence tokens

The file is `~/.ioassistant/secrets.env` (in the user's home folder, outside any project).

1. If it does not exist, create it (never overwrite an existing one):
   ```bash
   mkdir -p "$HOME/.ioassistant" && [ -e "$HOME/.ioassistant/secrets.env" ] || printf 'JIRA_EMAIL=paste_your_atlassian_email_here\nJIRA_API_TOKEN=paste_your_jira_token_here\nCONFLUENCE_API_TOKEN=paste_your_confluence_token_here\n' > "$HOME/.ioassistant/secrets.env"
   ```
2. Explain how to create each token (Jira is an Atlassian Cloud API token, Confluence a personal access token on our own server):
   - **Jira:** open https://id.atlassian.com/manage-profile/security/api-tokens → **Create API token** → name it "IO Project Assistant" → **Create** → copy the token. Also put the email you sign in to https://sectigo.atlassian.net/ with in `JIRA_EMAIL`.
   - **Confluence:** open https://confluence.comodoca.net/ → your avatar → **Settings** → **Personal Access Tokens** → **Create token** → copy it.
3. Open the file for them: Windows `notepad "$HOME/.ioassistant/secrets.env"`; Mac `open -e "$HOME/.ioassistant/secrets.env"`. They replace each `paste_..._here` with the email or token (no spaces, no quotes), save and close Notepad, then tell you "done".
4. Test without showing the tokens; print only the HTTP status:
   ```bash
   set -a; . "$HOME/.ioassistant/secrets.env"; set +a
   curl -s -o /dev/null -w "Jira %{http_code}\n" -u "$JIRA_EMAIL:$JIRA_API_TOKEN" https://sectigo.atlassian.net/rest/api/3/myself
   curl -s -o /dev/null -w "Confluence %{http_code}\n" -H "Authorization: Bearer $CONFLUENCE_API_TOKEN" https://confluence.comodoca.net/rest/api/user/current
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

Tell the user the run also needs read access to the Daily Ops StandUp and Rubrik Project SyncUp Teams chats, the I&O Project Roadmap on SharePoint, and write access to the "AI Test SharePoint Folder" and the Confluence space CO. Missing access does not stop the run; it shows up as a data gap in the report.

Finish with the checklist and, if everything is ✅, say: "You're ready. Type `/ioproject-assistant:run-report` to make today's report."
