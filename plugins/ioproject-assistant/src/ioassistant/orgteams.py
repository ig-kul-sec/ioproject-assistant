"""Team roster (reporting lines from Ardoq) used to group sprint tickets by team."""
from __future__ import annotations

import json
import re
import unicodedata
from pathlib import Path

OTHER = "Other"
ROSTER_PATH = Path(__file__).resolve().parents[2] / "config" / "org-teams.json"


def _key(value) -> str:
    """Name or email normalised for matching: no accents, lower case, single spaces."""
    text = unicodedata.normalize("NFKD", str(value or "")).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().lower()


def load(data: dict | None = None) -> dict:
    """Roster for the report: `data["org_teams"]` (fresh from Ardoq in this run) when present, else the bundled
    snapshot. Adds `live` (True when it came from the run) so the report can flag a static snapshot."""
    fresh = (data or {}).get("org_teams")
    if isinstance(fresh, dict) and fresh.get("teams"):
        return {**fresh, "live": True}
    try:
        roster = json.loads(ROSTER_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        roster = {"teams": []}
    return {**roster, "live": False}


def team_index(roster: dict) -> dict:
    """Map normalised person name or email -> team name (the manager belongs to the team too)."""
    index = {}
    for team in roster.get("teams", []):
        people = [{"name": team.get("manager"), "email": team.get("manager_email")}, *team.get("members", [])]
        for person in people:
            for field in ("name", "email"):
                if person.get(field):
                    index[_key(person[field])] = team["name"]
    return index


def idle(roster: dict, assignees) -> dict:
    """Per team, the members (not the manager) who are not the assignee of any of the given tickets.
    Matches by name or email like team_of. Returns {team name: [name, ...]} in roster order, names sorted."""
    busy = {_key(a) for a in assignees if a}
    return {
        team["name"]: sorted(
            (m["name"] for m in team.get("members", []) if _key(m.get("name")) not in busy and _key(m.get("email")) not in busy),
            key=_key,
        )
        for team in roster.get("teams", [])
    }


def headcount(team: dict) -> int:
    return len(team.get("members", [])) + (1 if team.get("manager") else 0)


def team_of(index: dict, assignee) -> str:
    """Team for a Jira assignee (display name or email); OTHER when not under one of the four managers."""
    return index.get(_key(assignee), OTHER)
