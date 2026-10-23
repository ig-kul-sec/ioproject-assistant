"""Tickets added to or removed from the active sprint after its first day, from the Jira change history."""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
from zoneinfo import ZoneInfo

TZ = ZoneInfo("America/New_York")  # same zone as the report
BOARD_ID = 485
JIRA_SITE = "https://projects.sectigo.net"
PAGE = 100
SECRETS = Path.home() / ".ioassistant" / "secrets.env"


def _ids(value) -> list:
    return [s.strip() for s in str(value or "").split(",") if s.strip()]


def _local(value):
    try:
        return datetime.fromisoformat(str(value)).astimezone(TZ)
    except (TypeError, ValueError):
        return None


def extract(issues: list, sprint_id, start: str, base: str = JIRA_SITE, members=()) -> list:
    """One row per add/remove of `sprint_id` made on the 2nd day of the sprint or later (`start` is yyyy-mm-dd,
    day 1). `issues` are Jira issues with the changelog expanded; `members` are the keys currently in the sprint.
    A move between sprints shows as a removal from one and an addition to the other; `other_sprint` names the
    sprint it came from or went to. A current member created on day 2 or later with no Sprint history entry was
    created straight into the sprint: it counts as added by its creator on the creation date."""
    cutoff = date.fromisoformat(start) + timedelta(days=1)
    sid, rows = str(sprint_id), []
    for issue in issues:
        fields = issue.get("fields") or {}
        mark = len(rows)
        for hist in (issue.get("changelog") or {}).get("histories", []):
            when = _local(hist.get("created"))
            if not when or when.date() < cutoff:
                continue
            for item in hist.get("items", []):
                if item.get("field") != "Sprint":
                    continue
                before, after = _ids(item.get("from")), _ids(item.get("to"))
                if (sid in before) == (sid in after):
                    continue
                added = sid in after
                names = {**dict(zip(before, str(item.get("fromString") or "").split(", "))),
                         **dict(zip(after, str(item.get("toString") or "").split(", ")))}
                other = [names.get(i, i) for i in (before if added else after) if i != sid]
                rows.append({
                    "key": issue.get("key"), "url": f"{base}/browse/{issue.get('key')}",
                    "name": fields.get("summary"), "status": (fields.get("status") or {}).get("name"),
                    "assignee": (fields.get("assignee") or {}).get("displayName"),
                    "action": "added" if added else "removed", "date": when.date().isoformat(),
                    "by": (hist.get("author") or {}).get("displayName"),
                    "other_sprint": ", ".join(other) or None,
                })
        made = _local(fields.get("created"))
        if (issue.get("key") in members and made and made.date() >= cutoff
                and not any(r["action"] == "added" for r in rows[mark:])):
            rows.append({
                "key": issue.get("key"), "url": f"{base}/browse/{issue.get('key')}",
                "name": fields.get("summary"), "status": (fields.get("status") or {}).get("name"),
                "assignee": (fields.get("assignee") or {}).get("displayName"),
                "action": "added", "date": made.date().isoformat(),
                "by": (fields.get("creator") or {}).get("displayName"), "other_sprint": None,
            })
    return sorted(rows, key=lambda r: (r["date"], str(r["key"]), r["action"]))


def _token() -> str:
    token = os.environ.get("JIRA_API_TOKEN")
    if not token and SECRETS.exists():
        for line in SECRETS.read_text(encoding="utf-8").splitlines():
            name, _, value = line.partition("=")
            if name.strip() == "JIRA_API_TOKEN":
                token = value.strip().strip("\"'")
    if not token:
        raise SystemExit("JIRA_API_TOKEN is not set (see ~/.ioassistant/secrets.env)")
    return token


def _get(site: str, path: str, params: dict, token: str) -> dict:
    url = f"{site}{path}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}", "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as resp:  # read-only GET
        return json.loads(resp.read().decode("utf-8"))


def fetch(site: str, sprint_name: str, start: str) -> list:
    """Changes of the active board sprint called `sprint_name`; raises SystemExit when it cannot be read."""
    token = _token()
    members: set = set()
    try:
        sprints = _get(site, f"/rest/agile/1.0/board/{BOARD_ID}/sprint", {"state": "active"}, token).get("values", [])
        match = next((s for s in sprints if s.get("name") == sprint_name), None)
        if not match:
            raise SystemExit(f"sprint {sprint_name!r} is not an active sprint on board {BOARD_ID}")
        fields = "summary,status,assignee,created,creator"
        # tickets removed since day 1 are only on the board; Done ones may be missing there, so also read the sprint
        issues = {}
        for path, extra in ((f"/rest/agile/1.0/board/{BOARD_ID}/issue", {"jql": f'updated >= "{start}"'}),
                            (f"/rest/agile/1.0/sprint/{match['id']}/issue", {})):
            at = 0
            while True:
                page = _get(site, path, {**extra, "fields": fields, "expand": "changelog",
                                         "startAt": at, "maxResults": PAGE}, token).get("issues", [])
                for issue in page:
                    issues.setdefault(issue["key"], issue)
                    if path.startswith("/rest/agile/1.0/sprint"):
                        members.add(issue["key"])
                if len(page) < PAGE:
                    break
                at += PAGE
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Jira answered HTTP {exc.code} (for 401/403 check JIRA_API_TOKEN)")
    except OSError as exc:  # network, VPN
        raise SystemExit(f"Jira not reachable: {exc}")
    return extract(list(issues.values()), match["id"], start, site, members)


def build(data_path: Path) -> Path:
    """Add `sprint.changes` to the run's data.json."""
    raw = data_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    sprint = data.get("sprint") or {}
    if not sprint.get("name") or not sprint.get("start"):
        raise SystemExit("data.json has no current sprint name/start")
    parts = urlsplit(str(data.get("jira_base_url") or JIRA_SITE))
    sprint["changes"] = fetch(f"{parts.scheme}://{parts.netloc}", sprint["name"], sprint["start"])
    data["sprint"] = sprint
    text = json.dumps(data, indent=1, ensure_ascii=False)  # the layout the run's data.json is written in
    if b"\r\n" in raw:
        text = text.replace("\n", "\r\n")
    data_path.write_bytes(text.encode("utf-8"))
    return data_path
