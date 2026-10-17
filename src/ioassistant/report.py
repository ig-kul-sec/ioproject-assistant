"""Render the IO Project Assistant HTML status report from merged run data."""
from __future__ import annotations

import json
from datetime import date
from html import escape
from pathlib import Path

NA = "n/a"


def _t(value) -> str:
    return escape(str(value)) if value not in (None, "") else NA


def _safe_url(url) -> str | None:
    """Only http(s) links are made clickable; anything else is rendered as text."""
    url = str(url or "")
    return url if url.lower().startswith(("http://", "https://")) else None


def _link(label, url) -> str:
    safe = _safe_url(url)
    if not safe:
        return _t(label or url)
    return f'<a href="{escape(safe, quote=True)}" target="_blank" rel="noopener">{_t(label or safe)}</a>'


def _days(start, end):
    try:
        return (date.fromisoformat(end) - date.fromisoformat(start)).days + 1
    except (TypeError, ValueError):
        return None


def _anchor(name) -> str:
    return escape(str(name or "project").replace(" ", "-"), quote=True)


def _sprint(sprint: dict) -> str:
    if not sprint:
        return "<p>No sprint data.</p>"
    dur = _days(sprint.get("start"), sprint.get("end"))
    rows = "".join(
        f"<tr><td>{_link(t.get('key'), t.get('url'))}</td><td>{_t(t.get('summary'))}</td>"
        f"<td>{_t(t.get('status'))}</td><td>{_t(t.get('assignee'))}</td><td>{_t(t.get('due'))}</td></tr>"
        for t in sprint.get("tickets", [])
    )
    return (
        f"<p><b>{_t(sprint.get('name'))}</b>: {_t(sprint.get('start'))} to {_t(sprint.get('end'))}"
        f" ({dur if dur is not None else NA} days)</p>"
        "<table><tr><th>Ticket</th><th>Summary</th><th>Status</th><th>Responsible</th><th>Due</th></tr>"
        f"{rows}</table>"
    )


def _links(links: dict) -> str:
    parts = [
        f"{escape(source)}: {_link(it.get('label'), it.get('url'))}"
        for source, items in (links or {}).items()
        for it in items or []
    ]
    return " &middot; ".join(parts) or NA


def _project(p: dict) -> str:
    notes = "".join(f"<li>{_t(n)}</li>" for n in p.get("notes", [])) or f"<li>{NA}</li>"
    actions = "".join(
        f"<li>{_t(a.get('text'))} &mdash; <b>{_t(a.get('owner'))}</b> (due {_t(a.get('due'))})</li>"
        for a in p.get("action_items", [])
    ) or f"<li>{NA}</li>"
    risks = "".join(f"<li>{_t(r)}</li>" for r in p.get("risks", [])) or f"<li>{NA}</li>"
    d = p.get("dates") or {}
    return (
        f'<section id="{_anchor(p.get("name"))}"><h3>{_t(p.get("name"))}</h3>'
        f"<h4>Latest notes</h4><ul>{notes}</ul>"
        f"<p><b>Progress:</b> {_t(p.get('progress'))}<br><b>Timeline:</b> {_t(p.get('timeline'))}<br>"
        f"<b>Dates:</b> {_t(d.get('start'))} to {_t(d.get('end'))}</p>"
        f"<h4>Action items</h4><ul>{actions}</ul><h4>Risks</h4><ul>{risks}</ul>"
        f"<p><b>Sources:</b> {_links(p.get('links'))}</p></section>"
    )


def render(data: dict, title: str) -> str:
    projects = data.get("projects", [])
    toc = "".join(f'<li><a href="#{_anchor(p.get("name"))}">{_t(p.get("name"))}</a></li>' for p in projects)
    gaps = "".join(f"<li>{_t(g)}</li>" for g in data.get("gaps", []))
    return (
        f"<!doctype html><html lang='en'><head><meta charset='utf-8'><title>{escape(title)}</title>"
        "<style>body{font:14px system-ui,sans-serif;max-width:1000px;margin:2rem auto;padding:0 1rem}"
        "table{border-collapse:collapse;width:100%}th,td{border:1px solid #ccc;padding:4px 8px;text-align:left}"
        "section{border-top:1px solid #ddd;margin-top:1rem}</style></head><body>"
        f"<h1>{escape(title)}</h1><p>Generated: {_t(data.get('generated_at'))}</p>"
        f"<h2>Sprint status</h2>{_sprint(data.get('sprint') or {})}"
        f"<h2>Project status</h2><ul>{toc}</ul>{''.join(_project(p) for p in projects)}"
        + (f"<h2>Data gaps</h2><ul>{gaps}</ul>" if gaps else "")
        + "</body></html>"
    )


def build(data_path: Path) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = data_path.parent / f"{run_id}.html"
    out.write_text(render(data, run_id), encoding="utf-8")
    return out
