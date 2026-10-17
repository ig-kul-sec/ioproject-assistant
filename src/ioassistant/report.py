"""Render the IO Project Assistant HTML status report from merged run data."""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html import escape
from pathlib import Path

from . import brand
from . import __version__

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


RAG = {
    "on track": ("On track", "ok"), "on-track": ("On track", "ok"), "green": ("On track", "ok"),
    "at risk": ("At risk", "risk"), "at-risk": ("At risk", "risk"), "amber": ("At risk", "risk"),
    "off track": ("Off track", "off"), "off-track": ("Off track", "off"), "red": ("Off track", "off"),
}
DONE_WORDS = ("done", "closed", "resolved", "complete")
TOP_NOTES = 3


def _rag(p: dict) -> tuple[str, str]:
    return RAG.get(str(p.get("status") or "").strip().lower(), ("Not rated", "na"))


def _pill(p: dict) -> str:
    label, cls = _rag(p)
    return f'<span class="pill {cls}">{label}</span>'


def _card(label, value, sub="") -> str:
    return (
        f'<div class="kpi"><div class="kpi-v">{value}</div><div class="kpi-l">{escape(label)}</div>'
        + (f'<div class="kpi-s">{sub}</div>' if sub else "")
        + "</div>"
    )


def _sprint(sprint: dict) -> str:
    if not sprint:
        return "<p>No sprint data.</p>"
    dur = _days(sprint.get("start"), sprint.get("end"))
    tickets = sprint.get("tickets", [])
    done = sum(1 for t in tickets if any(w in str(t.get("status") or "").lower() for w in DONE_WORDS))
    pct = f"{round(100 * done / len(tickets))}%" if tickets else NA
    rows = "".join(
        f"<tr><td>{_link(t.get('key'), t.get('url'))}</td><td>{_t(t.get('summary'))}</td>"
        f"<td>{_t(t.get('status'))}</td><td>{_t(t.get('assignee'))}</td><td>{_t(t.get('due'))}</td></tr>"
        for t in tickets
    )
    return (
        f"<p><b>{_t(sprint.get('name'))}</b>: {_t(sprint.get('start'))} to {_t(sprint.get('end'))}"
        f" ({dur if dur is not None else NA} days). {done} of {len(tickets)} tickets done ({pct}).</p>"
        f"<details><summary>All {len(tickets)} sprint tickets</summary>"
        "<table><tr><th>Ticket</th><th>Summary</th><th>Status</th><th>Responsible</th><th>Due</th></tr>"
        f"{rows}</table></details>"
    )


def _links(links: dict) -> str:
    parts = [
        f"{escape(source)}: {_link(it.get('label'), it.get('url'))}"
        for source, items in (links or {}).items()
        for it in items or []
    ]
    return " &middot; ".join(parts) or NA


def _ul(items: list[str]) -> str:
    return "<ul>" + "".join(items) + "</ul>" if items else f"<p>{NA}</p>"


AUTHOR_EMAIL = "igor.kulyk@sectigo.com"
REPO_URL = "https://github.com/ig-kul-sec/ioproject-assistant"
JIRA_BROWSE = "https://projects.sectigo.net/browse/"
KEY_RE = re.compile(r"^[A-Z][A-Z0-9]+-\d+$")
SOURCE_TYPES = ("teams", "sharepoint", "confluence", "jira")


def _ticket_link(ref, base: str) -> str:
    """Ticket reference (key string or {key,url}) as a hyperlink; plain text if it cannot be linked."""
    if isinstance(ref, dict):
        key, url = ref.get("key"), ref.get("url")
    else:
        key, url = ref, None
    key = str(key or "").strip()
    if not url and KEY_RE.match(key):
        url = base + key
    return _link(key, url) if key else NA


def _is_done(ticket: dict) -> bool:
    return any(w in str(ticket.get("status") or "").lower() for w in DONE_WORDS)


def _h(n: int, text: str) -> str:
    return f'<h4 class="sec"><span>{n}</span> {escape(text)}</h4>'


def _link_list(items) -> str:
    rows = "".join(f"<li>{_link(it.get('label'), it.get('url'))}</li>" for it in items or [])
    return f"<ul>{rows}</ul>" if rows else f"<p>{NA}</p>"


def _summary(p: dict, base: str) -> str:
    items = p.get("summary")
    if not items:  # fall back to the latest notes when the merge did not write a summary
        items = [{"text": n} for n in p.get("notes", [])[:TOP_NOTES]]
    out = []
    for it in items:
        it = it if isinstance(it, dict) else {"text": it}
        refs = ", ".join(_ticket_link(k, base) for k in it.get("tickets") or [])
        out.append(f"<li>{_t(it.get('text'))}" + (f" <span class='refs'>({refs})</span>" if refs else "") + "</li>")
    risks = [f"<li>{_t(r)}</li>" for r in p.get("risks", [])]
    return _ul(out) + (f"<p class='lbl'>Risks</p>{_ul(risks)}" if risks else "")


def _jira_updates(p: dict, base: str) -> str:
    ju = p.get("jira_updates") or {}
    change, create = ju.get("change") or [], ju.get("create") or []
    if not change and not create:
        return "<p>No Jira updates identified.</p>"
    html = ""
    if change:
        rows = "".join(
            f"<tr><td>{_ticket_link(c, base)}</td><td>{_t(c.get('type'))}</td><td>{_t(c.get('detail'))}</td></tr>"
            for c in change
        )
        html += (
            "<p class='lbl'>Existing tickets to change</p>"
            "<table><tr><th>Ticket</th><th>Change</th><th>What to do</th></tr>" + rows + "</table>"
        )
    if create:
        rows = "".join(
            f"<tr><td>{_t(c.get('name'))}</td><td>{_t(c.get('description'))}</td><td>{_t(c.get('start'))}</td>"
            f"<td>{_t(c.get('end'))}</td><td>{_t(c.get('owner'))}</td></tr>"
            for c in create
        )
        html += (
            "<p class='lbl'>New tickets to create</p>"
            "<table><tr><th>Name</th><th>Description</th><th>Start</th><th>End</th><th>Responsible</th></tr>"
            + rows + "</table>"
        )
    return html


def _sources(p: dict) -> str:
    links = p.get("links") or {}
    counts = ", ".join(f"{escape(k)} ({len(v)})" for k, v in links.items() if v)
    other = [
        f"<li>{escape(k)}: {_link(it.get('label'), it.get('url'))}</li>"
        for k, v in links.items() if k not in SOURCE_TYPES for it in v or []
    ]
    return f"<p>Sources used: {counts or NA}.</p>" + (_ul(other) if other else "")


def _tickets(p: dict, base: str) -> str:
    ts = sorted(p.get("tickets") or [], key=lambda t: (_is_done(t), not t.get("epic")))
    if not ts:
        return f"<p>{NA}</p>"
    rows = "".join(
        f"<tr class=\"{'done' if _is_done(t) else 'active'}\"><td>{_ticket_link(t, base)}</td>"
        f"<td>{_t(t.get('name') or t.get('summary'))}</td><td>{_t(t.get('status'))}</td>"
        f"<td>{_t(t.get('assignee'))}</td><td>{_t(t.get('start'))}</td><td>{_t(t.get('end') or t.get('due'))}</td>"
        f"<td>{', '.join(_ticket_link(r, base) for r in t.get('related') or []) or NA}</td></tr>"
        for t in ts
    )
    return (
        "<table class='tix'><tr><th>Ticket #</th><th>Ticket name</th><th>Status</th><th>Responsible</th>"
        f"<th>Start</th><th>End</th><th>Related tickets</th></tr>{rows}</table>"
    )


def _project(p: dict, base: str = JIRA_BROWSE) -> str:
    links = p.get("links") or {}
    return (
        f'<section class="card" id="{_anchor(p.get("name"))}">'
        f'<div class="card-h"><h3>{_t(p.get("name"))}</h3>{_pill(p)}</div>'
        f"{_h(1, 'Project updates (summary)')}{_summary(p, base)}"
        f"{_h(2, 'Jira task updates needed')}{_jira_updates(p, base)}"
        f"{_h(3, 'Project sources')}{_sources(p)}"
        f"{_h(4, 'Project meeting chats')}{_link_list(links.get('teams'))}"
        f"{_h(5, 'Project SharePoint folder')}{_link_list(links.get('sharepoint'))}"
        f"{_h(6, 'Project Confluence page')}{_link_list(links.get('confluence'))}"
        f"{_h(7, 'Jira tickets for this project')}{_tickets(p, base)}</section>"
    )


EXTRA_CSS = """
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:16px}
.kpi{background:var(--forest);color:var(--off-white);border-radius:12px;padding:18px 20px}
.kpi-v{font:700 36px/1 'Urbanist',Arial,sans-serif;color:var(--spearmint)}
.kpi-l{margin-top:6px;font-weight:600}.kpi-s{font-size:12px;opacity:.8}
.pill{display:inline-block;border-radius:999px;padding:2px 12px;font-size:13px;font-weight:600;white-space:nowrap}
.pill.ok{background:var(--spearmint);color:var(--forest)}
.pill.risk{background:var(--scout);color:var(--off-black)}
.pill.off{background:var(--coral);color:var(--off-black)}
.pill.na{border:1px solid var(--off-black);color:var(--off-black)}
.card{background:var(--off-white);border:1px solid var(--forest);border-radius:12px;padding:20px 24px;margin:20px 0}
.card-h{display:flex;justify-content:space-between;align-items:center;gap:12px}
.card h3{font-size:22px}.meta{margin:.5rem 0 0;font-size:13px}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}
h4.sec{display:flex;align-items:center;gap:8px;margin:1.4rem 0 .4rem;font-size:15px;border-bottom:1px solid var(--forest);padding-bottom:4px}
h4.sec span{background:var(--forest);color:var(--spearmint);border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:12px}
.lbl{font-weight:600;margin:.6rem 0 .2rem}.refs{font-size:13px}
table.tix tr.done td{opacity:.6}
ul{margin:.25rem 0;padding-left:1.2rem}
details{margin:.5rem 0}summary{cursor:pointer;color:var(--forest);font-weight:600}
@media print{header.top{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


REPORT_TZ = "America/New_York"


def _range(window) -> str:
    """'Analysis range: from yyyy.mm.dd till yyyy.mm.dd hh:mm EST (24h)'; the zone label is EST or EDT as in force."""
    try:
        tz = ZoneInfo(REPORT_TZ)
        start = datetime.fromisoformat(str(window["from"]).replace("Z", "+00:00")).astimezone(tz)
        end = datetime.fromisoformat(str(window["to"]).replace("Z", "+00:00")).astimezone(tz)
    except (TypeError, KeyError, ValueError):
        return f"Analysis range: {NA}"
    return f"Analysis range: from {start:%Y.%m.%d} till {end:%Y.%m.%d %H:%M} {end.tzname()} (24h)"


def _footer() -> str:
    return (
        "<footer><p><b>IO Project Assistant</b> &nbsp;|&nbsp; "
        f"Version: {escape(__version__)} &nbsp;|&nbsp; Author: "
        f'<a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a> &nbsp;|&nbsp; '
        f'GitHub: <a href="{REPO_URL}" target="_blank" rel="noopener">{REPO_URL}</a></p>'
        "<p>sectigo.com &nbsp;|&nbsp; Sectigo&copy; 2026. All rights reserved.</p></footer>"
    )


def render(data: dict, title: str) -> str:
    base = str(data.get("jira_base_url") or JIRA_BROWSE)
    projects = data.get("projects", [])
    gaps = data.get("gaps", [])
    attention = sum(1 for p in projects if _rag(p)[1] in ("risk", "off"))
    jira_todo = sum(
        len((p.get("jira_updates") or {}).get("change") or []) + len((p.get("jira_updates") or {}).get("create") or [])
        for p in projects
    )
    sprint = data.get("sprint") or {}
    tickets = sprint.get("tickets", [])
    done = sum(1 for t in tickets if any(w in str(t.get("status") or "").lower() for w in DONE_WORDS))
    kpis = (
        _card("Projects reported", len(projects))
        + _card("Need attention", attention, "at risk or off track")
        + _card("Jira updates needed", jira_todo, "change or create")
        + _card("Sprint tickets done", f"{done}/{len(tickets)}", escape(str(sprint.get("name") or "")))
        + _card("Data gaps", len(gaps), "see end of report")
    )
    glance = "".join(
        f'<tr><td><a href="#{_anchor(p.get("name"))}">{_t(p.get("name"))}</a></td><td>{_pill(p)}</td>'
        f'<td>{_t(p.get("progress"))}</td><td>{_t(p.get("timeline"))}</td>'
        f'<td>{_t((p.get("risks") or [None])[0])}</td></tr>'
        for p in projects
    )
    gap_html = (
        f"<h2>Data gaps</h2><details><summary>{len(gaps)} gaps in this run</summary>"
        + _ul([f"<li>{_t(g)}</li>" for g in gaps]) + "</details>"
        if gaps else ""
    )
    return (
        brand.head(title, EXTRA_CSS)
        + "<body>"
        + brand.banner("I&O project status report", f"{title}  |  Generated {data.get('generated_at') or NA}",
                       _range(data.get("window")))
        + "<main class='wrap'>"
        f"<h2>Summary</h2><div class='kpis'>{kpis}</div>"
        "<h2>Projects at a glance</h2>"
        "<table><tr><th>Project</th><th>Status</th><th>Progress</th><th>Timeline</th><th>Top risk</th></tr>"
        f"{glance}</table>"
        f"<h2>Project status</h2>{''.join(_project(p, base) for p in projects)}"
        f"<h2>Sprint status</h2>{_sprint(sprint)}"
        f"{gap_html}{_footer()}"
        "</main></body></html>"
    )


def build(data_path: Path) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = data_path.parent / f"{run_id}.html"
    out.write_text(render(data, run_id), encoding="utf-8")
    return out
