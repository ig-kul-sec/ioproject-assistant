"""Fixed resources per project (Jira epic and initiative, Confluence, Planner, Teams chat) from config/project-resources.json.

Both reports add them to what a run finds itself: "Project sources" (status report) and "Key project resources"
(leadership report). Standard library only."""
from __future__ import annotations

import json
import re
from pathlib import Path

PATH = Path(__file__).resolve().parents[2] / "config" / "project-resources.json"
KINDS = ("epic", "initiative", "confluence", "planner", "chat")
KEY_IN_URL = re.compile(r"/browse/([A-Z][A-Z0-9]+-\d+)(?:[/?#]|$)")


def load(path: Path = PATH) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))["projects"]


def _has_word(text: str, word: str) -> bool:
    return bool(re.search(rf"(?<!\w){re.escape(word.lower())}(?!\w)", text))


def _link(item: dict) -> dict:
    """{kind, label, url, key}: a Jira link takes its key from the URL and uses it as the label."""
    kind, url = item["kind"], item["url"]
    if kind not in KINDS:
        raise ValueError(f"project-resources.json: unknown kind {kind!r} (use one of {', '.join(KINDS)})")
    match = KEY_IN_URL.search(url) if kind in ("epic", "initiative") else None
    key = match.group(1) if match else None
    return {"kind": kind, "label": item.get("label") or key or url, "url": url, "key": key}


def find(name, entries: list[dict] | None = None) -> list[dict]:
    """The links of the first entry with a match word in the project name (whole words, case-insensitive); [] when none."""
    low = str(name or "").lower()
    for entry in load() if entries is None else entries:
        if any(_has_word(low, w) for w in entry.get("match", [])):
            return [_link(x) for x in entry.get("links", [])]
    return []


def of_kind(links: list[dict], kind: str) -> list[dict]:
    return [x for x in links if x["kind"] == kind]
