"""Complete ticket lists of the active sprint and the open past sprints, read from Jira (read-only)."""
from __future__ import annotations

import json
from pathlib import Path
from urllib.parse import urlsplit
import urllib.error

from .sprintchanges import BOARD_ID, JIRA_SITE, PAGE, _get, _token

# customfield_10023 is "Target end": IOSP tickets keep their end date there and leave "Due date" empty.
FIELDS = "summary,status,assignee,duedate,customfield_10023"


def _row(issue: dict, base: str, old: dict | None) -> dict:
    """The data.json ticket shape; fields the collector added (epic, start, ...) are kept."""
    fields = issue.get("fields") or {}
    return {**(old or {}),
            "key": issue["key"], "url": f"{base}/browse/{issue['key']}", "name": fields.get("summary"),
            "status": (fields.get("status") or {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"), "due": fields.get("duedate") or fields.get("customfield_10023")}


def fetch(site: str, sprint_id, token: str) -> list:
    """Every issue of the sprint, paged until Jira's total is reached; raises SystemExit when the count falls short."""
    issues, at, total = [], 0, 0
    while True:
        page = _get(site, f"/rest/agile/1.0/sprint/{sprint_id}/issue",
                    {"fields": FIELDS, "startAt": at, "maxResults": PAGE}, token)
        total = page.get("total", 0)
        issues += page.get("issues", [])
        at += len(page.get("issues", []))
        if not page.get("issues") or at >= total:
            break
    if len(issues) != total:
        raise SystemExit(f"sprint {sprint_id}: read {len(issues)} of {total} tickets")
    return issues


def merge(tickets: list, issues: list, base: str = JIRA_SITE) -> list:
    """Jira's list in Jira's order, taking over what the collector already recorded for each key."""
    known = {str(t.get("key")): t for t in tickets or []}
    return [_row(i, base, known.get(i["key"])) for i in issues]


def fill_ids(data: dict, sprints: list) -> None:
    """Give the current and past sprints that lack an `id` the Agile id of the board sprint with the same name."""
    by_name = {str(s.get("name")): s["id"] for s in sprints if s.get("id") is not None}
    for s in [data.get("sprint") or {}, *(data.get("past_sprints") or [])]:
        if not s.get("id") and s.get("name") in by_name:
            s["id"] = by_name[s["name"]]


def build(data_path: Path) -> Path:
    """Replace `sprint.tickets` and each `past_sprints[].tickets` in the run's data.json with the full Jira list."""
    raw = data_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    sprint = data.get("sprint") or {}
    parts = urlsplit(str(data.get("jira_base_url") or JIRA_SITE))
    site = f"{parts.scheme}://{parts.netloc}"
    token = _token()
    try:
        if not sprint.get("id") or any(not p.get("id") for p in data.get("past_sprints") or []):
            # the Jira agent did not return the Agile sprint ids: look them up on the board by sprint name
            fill_ids(data, _get(site, f"/rest/agile/1.0/board/{BOARD_ID}/sprint", {"state": "active"}, token).get("values", []))
        if not sprint.get("id"):
            raise SystemExit(f"data.json has no current sprint id and sprint {sprint.get('name')!r} is not an active sprint on board {BOARD_ID}")
        for s in [sprint, *[p for p in data.get("past_sprints") or [] if p.get("id")]]:
            s["tickets"] = merge(s.get("tickets"), fetch(site, s["id"], token), site)
    except urllib.error.HTTPError as exc:
        raise SystemExit(f"Jira answered HTTP {exc.code} (for 401/403 check JIRA_EMAIL and JIRA_API_TOKEN)")
    except OSError as exc:  # network, VPN
        raise SystemExit(f"Jira not reachable: {exc}")
    text = json.dumps(data, indent=1, ensure_ascii=False)  # the layout the run's data.json is written in
    if b"\r\n" in raw:
        text = text.replace("\n", "\r\n")
    data_path.write_bytes(text.encode("utf-8"))
    return data_path
