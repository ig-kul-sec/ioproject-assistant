"""Render the RELEASE LOG section of the Confluence parent page from CHANGELOG.md (storage format, plain XHTML).

Only released versions (a dated `## [X.Y.Z] - yyyy-mm-dd` heading) are listed; "in development" sections are skipped.
Run it on the CHANGELOG.md of `main` (PROD), so the log shows what is deployed.
"""
from __future__ import annotations

import re
from html import escape
from pathlib import Path

HEADING = "RELEASE LOG"
INTRO = "Versions deployed to PROD (main), newest first. Source: CHANGELOG.md in the GitHub repository."

_VERSION_RE = re.compile(r"^##\s+\[([^\]]+)\]\s*(?:-\s*(\d{4}-\d{2}-\d{2}))?\s*(.*)$")
_CATEGORY_RE = re.compile(r"^###\s+(.+?)\s*$")
_BULLET_RE = re.compile(r"^[-*]\s+(.*)$")
_HEADING_RE = re.compile(r"<h([1-6])\b[^>]*>(.*?)</h\1>", re.IGNORECASE | re.DOTALL)


def parse(text: str) -> list[dict]:
    """CHANGELOG.md text -> released versions in file order: {version, date, categories: [(name, [item, ...])]}."""
    releases: list[dict] = []
    current: dict | None = None
    category: list | None = None
    item_open = False
    for line in text.splitlines():
        m = _VERSION_RE.match(line)
        if m:
            current, category, item_open = None, None, False
            if m.group(2):  # undated ("in development", "Unreleased") sections are not deployed
                current = {"version": m.group(1).strip(), "date": m.group(2), "categories": []}
                releases.append(current)
            continue
        if current is None:
            continue
        m = _CATEGORY_RE.match(line)
        if m:
            category = [m.group(1), []]
            current["categories"].append(category)
            item_open = False
            continue
        m = _BULLET_RE.match(line)
        if m:
            if category is None:
                category = ["Changes", []]
                current["categories"].append(category)
            category[1].append(m.group(1).strip())
            item_open = True
        elif line.strip() and line[:1].isspace() and item_open:  # wrapped bullet
            category[1][-1] += " " + line.strip()
        elif not line.strip():
            item_open = False
    return releases


def _inline(text: str) -> str:
    """Markdown inline (code, bold, links) -> XHTML; everything else is escaped."""
    out = []
    for i, part in enumerate(re.split(r"(`[^`]+`)", text)):
        if i % 2:
            out.append(f"<code>{escape(part[1:-1])}</code>")
            continue
        part = escape(part)
        part = re.sub(r"\[([^\]]+)\]\((https?://[^)\s]+)\)", r'<a href="\2">\1</a>', part)
        part = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", part)
        out.append(part)
    return "".join(out)


def _changes(release: dict) -> str:
    cells = []
    for name, items in release["categories"]:
        if not items:
            continue
        lis = "".join(f"<li>{_inline(item)}</li>" for item in items)
        cells.append(f"<p><strong>{escape(name)}</strong></p><ul>{lis}</ul>")
    return "".join(cells) or "<p>n/a</p>"


def render(releases: list[dict]) -> str:
    """The whole section: heading, one line of intro, and a Version | Date | Changes table, newest version first."""
    ordered = sorted(releases, key=lambda r: r["date"], reverse=True)  # stable: same-day releases keep file order (newest first)
    rows = "".join(
        f"<tr><td><strong>{escape(r['version'])}</strong></td><td>{escape(r['date'])}</td><td>{_changes(r)}</td></tr>"
        for r in ordered
    )
    table = (
        "<table><tbody><tr><th>Version</th><th>Date</th><th>Changes</th></tr>" + rows + "</tbody></table>"
        if rows else "<p>No released versions yet.</p>"
    )
    return f"<h2>{HEADING}</h2><p>{escape(INTRO)}</p>{table}"


def merge(page_body: str, section: str) -> str:
    """Put `section` into the page body: replace an existing RELEASE LOG section (from its heading up to the next heading of
    the same or a higher level, or the end), otherwise append it at the end. The rest of the page is left untouched."""
    for m in _HEADING_RE.finditer(page_body):
        if re.sub(r"<[^>]+>|&nbsp;|\s+", " ", m.group(2)).strip().upper() != HEADING:
            continue
        level = int(m.group(1))
        end = len(page_body)
        for nxt in _HEADING_RE.finditer(page_body, m.end()):
            if int(nxt.group(1)) <= level:
                end = nxt.start()
                break
        return page_body[: m.start()] + section + page_body[end:]
    return page_body + section


def build(changelog: Path, page_body: Path | None = None, out: Path | None = None) -> Path:
    """Write the RELEASE LOG section (or, with `page_body`, the page body with the section merged in) and return the file."""
    section = render(parse(changelog.read_text(encoding="utf-8")))
    text = merge(page_body.read_text(encoding="utf-8"), section) if page_body else section
    out = out or Path("output") / "release-log" / ("page_body.xhtml" if page_body else "release_log.xhtml")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(text.encode("utf-8"))
    return out
