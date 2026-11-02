"""Complete ticket lists of the active sprint and the open past sprints, read from Jira (read-only)."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from pathlib import Path
from urllib.parse import urlsplit
import urllib.error

from .sprintchanges import BOARD_ID, JIRA_SITE, PAGE, TZ, _get, _local, _token, board_sprints, period_of

# customfield_10023 is "Target end": IOSP tickets keep their end date there and leave "Due date" empty.
FIELDS = "summary,status,assignee,duedate,customfield_10023,resolutiondate"  # resolutiondate feeds the burndown chart


def _row(issue: dict, base: str, old: dict | None) -> dict:
    """The data.json ticket shape; fields the collector added (epic, start, ...) are kept."""
    fields = issue.get("fields") or {}
    return {**(old or {}),
            "key": issue["key"], "url": f"{base}/browse/{issue['key']}", "name": fields.get("summary"),
            "status": (fields.get("status") or {}).get("name"),
            "assignee": (fields.get("assignee") or {}).get("displayName"), "due": fields.get("duedate") or fields.get("customfield_10023"),
            "resolved": fields.get("resolutiondate")}


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


def _day(value) -> str | None:
    """yyyy-mm-dd (America/New_York) of a Jira timestamp, None when it is missing."""
    when = _local(value)
    return when.date().isoformat() if when else None


def roll_over(data: dict, sprints: list, today: date) -> str | None:
    """Jira keeps a sprint "active" until someone closes it, and the next one stays "future" until it is started.
    When the current sprint's end date is before `today`, the sprint that follows it becomes the current sprint
    (the earliest active or future board sprint that has not ended; ties by the numbers in the name) and the ended one
    is appended to `past_sprints`. Returns a note for the report's gaps, or None when nothing changed."""
    cur = data.get("sprint") or {}
    try:
        ended = date.fromisoformat(str(cur.get("end"))[:10]) < today
    except ValueError:
        return None  # no usable end date: keep the sprint as it is
    if not ended:
        return None
    past = data.get("past_sprints") or []
    known_ids = {str(s.get("id")) for s in [cur, *past] if s.get("id") is not None}
    known_names = {s.get("name") for s in [cur, *past]}
    found = []
    for s in sprints:
        if s.get("state") not in ("active", "future") or str(s.get("id")) in known_ids or s.get("name") in known_names:
            continue
        start, end = _day(s.get("startDate")), _day(s.get("endDate"))
        if end and date.fromisoformat(end) < today:
            continue  # ended too, still not closed: it stays with the past sprints
        found.append((start or "9999-12-31", tuple(int(n) for n in re.findall(r"\d+", str(s.get("name")))), s, start, end))
    if not found:
        return None
    _, _, nxt, start, end = min(found, key=lambda f: f[:2])
    assumed = ""
    if not (start and end):
        # not planned in Jira yet: same length as the sprint that ended, one week later
        try:
            first, last = date.fromisoformat(str(cur["start"])[:10]), date.fromisoformat(str(cur["end"])[:10])
            start = start or (first + timedelta(days=7)).isoformat()
            end = end or (date.fromisoformat(start) + (last - first)).isoformat()
            assumed = "; the dates are not set in Jira, assumed from the previous sprint"
        except (KeyError, ValueError):
            pass
    data["past_sprints"] = [*past, cur]
    data["sprint"] = {"id": nxt["id"], "name": nxt["name"], "start": start, "end": end, "tickets": []}
    return (f"Current sprint: {cur.get('name')} ended {cur.get('end')} but is still active in Jira; "
            f"the report uses {nxt['name']} ({start} to {end}) as the current sprint{assumed}.")


def build(data_path: Path) -> Path:
    """Replace `sprint.tickets` and each `past_sprints[].tickets` in the run's data.json with the full Jira list.
    First makes the sprint that covers the report day the current one (see `roll_over`)."""
    raw = data_path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    parts = urlsplit(str(data.get("jira_base_url") or JIRA_SITE))
    site = f"{parts.scheme}://{parts.netloc}"
    token = _token()
    period = period_of(data.get("window"))
    today = period[1].date() if period else datetime.now(TZ).date()
    try:
        sprints = board_sprints(site, token, "active,future")
        # the Jira agent may not have returned the Agile sprint ids: look them up on the board by sprint name
        fill_ids(data, sprints)
        note = roll_over(data, sprints, today)
        if note:
            data["gaps"] = [*(data.get("gaps") or []), note]
        sprint = data.get("sprint") or {}
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
