"""Render the IO Project Assistant HTML status report from merged run data."""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from zoneinfo import ZoneInfo
from html import escape, unescape
from pathlib import Path

from . import brand, spend

NA = "n/a"


def _t(value) -> str:
    return escape(str(value)) if value not in (None, "") else NA


ISO_DATE = re.compile(r"(?<![\w/.-])\d{4}-(\d{2})-(\d{2})(?:T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?(?![\w-])")
MD_DATE = re.compile(r"(?<![\w/.:-])(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?![\w-])")
TICKET_IN_TEXT = re.compile(r"(?<![\w/-])((?:IOSP|RM|COR)-\d+)(?![\w-])")


def _md(value) -> str:
    """Date as mm/dd; ISO dates and timestamps are converted, other text is returned as is."""
    text = str(value or "")
    m = re.fullmatch(r"\d{4}-(\d{2})-(\d{2})(?:T.*)?", text)
    return f"{m.group(1)}/{m.group(2)}" if m else text


def _dated(value) -> str:
    """Escaped text with dates shown as mm/dd (no ticket links, safe inside an anchor)."""
    text = escape(str(value))
    text = ISO_DATE.sub(lambda m: f"{m.group(1)}/{m.group(2)}", text)
    return MD_DATE.sub(lambda m: f"{m.group(1)}/{m.group(2)}", text)


def _rich(value, base: str = "") -> str:
    """Escaped free text with dates shown as mm/dd and Jira keys (IOSP/RM/COR) turned into links."""
    if value in (None, ""):
        return NA
    text = _dated(value)
    return TICKET_IN_TEXT.sub(lambda m: _ticket_link(m.group(1), base or JIRA_BROWSE), text)


def _date_td(value) -> str:
    """Table cell with a date as mm/dd; the ISO value is kept for correct column sorting."""
    text = str(value or "")
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}.*", text):
        return f'<td data-s="{escape(text[:10], quote=True)}">{_rich(value)}</td>'
    return f"<td>{_rich(value)}</td>"


def _safe_url(url) -> str | None:
    """Only http(s) links are made clickable; anything else is rendered as text."""
    url = str(url or "")
    return url if url.lower().startswith(("http://", "https://")) else None


def _link(label, url) -> str:
    safe = _safe_url(url)
    if not safe:
        return _dated(label or url) if (label or url) else NA
    return f'<a href="{escape(safe, quote=True)}" target="_blank" rel="noopener">{_dated(label) if label else escape(safe)}</a>'


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
    board = _link("JIRA ScrumBoard Link", brand.JIRA_BOARD_URL)
    if not sprint:
        return f"<p>{board}</p><p>No sprint data.</p>"
    dur = _days(sprint.get("start"), sprint.get("end"))
    tickets = sprint.get("tickets", [])
    done = sum(1 for t in tickets if any(w in str(t.get("status") or "").lower() for w in DONE_WORDS))
    pct = f"{round(100 * done / len(tickets))}%" if tickets else NA
    rows = "".join(
        f"<tr><td>{_link(t.get('key'), t.get('url'))}</td><td>{_t(t.get('summary'))}</td>"
        f"<td>{_t(t.get('status'))}</td><td>{_t(t.get('assignee'))}</td>{_date_td(t.get('due'))}</tr>"
        for t in tickets
    )
    return (
        f"<p>{board}</p>"
        f"<p><b>{_t(sprint.get('name'))}</b>: {_t(_md(sprint.get('start')))} to {_t(_md(sprint.get('end')))}"
        f" ({dur if dur is not None else NA} days). {done} of {len(tickets)} tickets done ({pct}).</p>"
        f"<details class=\"sub\"><summary>All {len(tickets)} sprint tickets</summary>"
        "<table><tr><th>Ticket</th><th>Summary</th><th>Status</th><th>Responsible</th><th>Due</th></tr>"
        f"{rows}</table></details>"
    )


def _links(links: dict) -> str:
    parts = [
        f"{_dated(source)}: {_link(it.get('label'), it.get('url'))}"
        for source, items in (links or {}).items()
        for it in items or []
    ]
    return " &middot; ".join(parts) or NA


def _ul(items: list[str]) -> str:
    return "<ul>" + "".join(items) + "</ul>" if items else f"<p>{NA}</p>"


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


def _sec(n: int, text: str, body: str) -> str:
    return f'<details class="sub" open><summary class="sec"><span>{n}</span> {escape(text)}</summary>{body}</details>'


def _unique_links(items) -> list[dict]:
    """Drop repeated URLs, then number labels that still repeat ("recap 10/14 (1)", "(2)") so each link reads distinct."""
    seen, out = set(), []
    for it in items or []:
        key = it.get("url") or it.get("label")
        if key in seen:
            continue
        seen.add(key)
        out.append(dict(it))
    totals: dict = {}
    for it in out:
        totals[it.get("label")] = totals.get(it.get("label"), 0) + 1
    counter: dict = {}
    for it in out:
        label = it.get("label")
        if label and totals[label] > 1:
            counter[label] = counter.get(label, 0) + 1
            it["label"] = f"{label} ({counter[label]})"
    return out


def _link_list(items) -> str:
    rows = "".join(f"<li>{_link(it.get('label'), it.get('url'))}</li>" for it in _unique_links(items))
    return f"<ul>{rows}</ul>" if rows else f"<p>{NA}</p>"


def _summary(p: dict, base: str) -> str:
    items = p.get("summary")
    if not items:  # fall back to the latest notes when the merge did not write a summary
        items = [{"text": n} for n in p.get("notes", [])[:TOP_NOTES]]
    out = []
    for it in items:
        it = it if isinstance(it, dict) else {"text": it}
        refs = ", ".join(_ticket_link(k, base) for k in it.get("tickets") or [])
        out.append(f"<li>{_rich(it.get('text'), base)}" + (f" <span class='refs'>({refs})</span>" if refs else "") + "</li>")
    risks = [f"<li>{_rich(r, base)}</li>" for r in p.get("risks", [])]
    return _ul(out) + (f"<p class='lbl'>Risks</p>{_ul(risks)}" if risks else "")


def _jira_updates(p: dict, base: str) -> str:
    ju = p.get("jira_updates") or {}
    change, create = ju.get("change") or [], ju.get("create") or []
    if not change and not create:
        return "<p>No Jira updates identified.</p>"
    html = ""
    if change:
        names = {str(t.get("key")): t.get("name") or t.get("summary") for t in p.get("tickets") or []}
        rows = "".join(
            f"<tr><td>{_ticket_link(c, base)}</td>"
            f"<td>{_rich(c.get('name') or c.get('summary') or names.get(str(c.get('key'))), base)}</td>"
            f"<td>{_t(c.get('type'))}</td><td>{_rich(c.get('detail'), base)}</td></tr>"
            for c in change
        )
        html += (
            "<p class='lbl'>Existing tickets to change</p>"
            "<table><tr><th>Ticket</th><th>Ticket name</th><th>Change</th><th>What to do</th></tr>" + rows + "</table>"
        )
    if create:
        rows = "".join(
            f"<tr><td>{_rich(c.get('name'), base)}</td><td>{_rich(c.get('description'), base)}</td>"
            f"{_date_td(c.get('start'))}{_date_td(c.get('end'))}<td>{_t(c.get('owner'))}</td></tr>"
            for c in create
        )
        html += (
            "<p class='lbl'>New tickets to create</p>"
            "<table><tr><th>Name</th><th>Description</th><th>Start</th><th>End</th><th>Responsible</th></tr>"
            + rows + "</table>"
        )
    return html


def _sources(p: dict) -> str:
    links = {k: _unique_links(v) for k, v in (p.get("links") or {}).items()}
    counts = ", ".join(f"{_dated(k)} ({len(v)})" for k, v in links.items() if v)
    other = [
        f"<li>{_dated(k)}: {_link(it.get('label'), it.get('url'))}</li>"
        for k, v in links.items() if k not in SOURCE_TYPES for it in v
    ]
    return f"<p>Sources used: {counts or NA}.</p>" + (_ul(other) if other else "")


def _tickets(p: dict, base: str) -> str:
    ts = sorted(p.get("tickets") or [], key=lambda t: (_is_done(t), not t.get("epic")))
    if not ts:
        return f"<p>{NA}</p>"
    rows = "".join(
        f"<tr class=\"{'done' if _is_done(t) else 'active'}\"><td>{_ticket_link(t, base)}</td>"
        f"<td>{_rich(t.get('name') or t.get('summary'), base)}</td><td>{_t(t.get('status'))}</td>"
        f"<td>{_t(t.get('assignee'))}</td>{_date_td(t.get('start'))}{_date_td(t.get('end') or t.get('due'))}"
        f"<td>{', '.join(_ticket_link(r, base) for r in t.get('related') or []) or NA}</td></tr>"
        for t in ts
    )
    return (
        "<table class='tix'><tr><th>Ticket #</th><th>Ticket name</th><th>Status</th><th>Responsible</th>"
        f"<th>Start</th><th>End</th><th>Related tickets</th></tr>{rows}</table>"
    )


# line icons (brand 6.3: single-weight stroke, rounded, currentColor)
ICON_COLLAPSE = "<path d='M7 4l5 5 5-5'/><path d='M7 20l5-5 5 5'/>"
ICON_EXPAND = "<path d='M7 9l5-5 5 5'/><path d='M7 15l5 5 5-5'/>"
ICON_TREE = "<path d='M3 6h18'/><path d='M7 12h14'/><path d='M11 18h10'/>"


def _tool(ident: str, label: str, icon: str) -> str:
    return (f"<button class='tool' id='{ident}'><svg viewBox='0 0 24 24' aria-hidden='true'>{icon}</svg>"
            f"{escape(label)}</button>")


NON_PROJECT_TYPES = ("Incident", "Problem", "Issue", "Change", "Maintenance", "Other")


OPS_TITLE = "Daily Ops operational health and incidents"


def _ops_tickets(tickets, base: str) -> str:
    """Related Jira tickets: keys or {key, url, status}; the status follows the link when known."""
    out = []
    for t in tickets or []:
        link = _ticket_link(t, base)
        status = t.get("status") if isinstance(t, dict) else None
        out.append(f"{link} ({escape(str(status))})" if status else link)
    return "<br>".join(out) or NA


def _non_project(items, base: str) -> str:
    """Daily Ops items not tied to a project (incidents, problems, issues...), newest first."""
    if not items:
        return "<p>No Daily Ops operational updates in this period.</p>"
    counts = ", ".join(
        f"{t}: {n}" for t in NON_PROJECT_TYPES
        if (n := sum(1 for it in items if (it.get("type") or "Other") == t))
    )
    rows = []
    for it in sorted(items, key=lambda i: str(i.get("date") or ""), reverse=True):
        item = f"<b>{_rich(it.get('title'), base)}</b>"
        if it.get("detail"):
            item += f"<br>{_rich(it.get('detail'), base)}"
        src = it.get("source") or {}
        rows.append(
            f"<tr>{_date_td(it.get('date'))}<td>{_t(it.get('type') or 'Other')}</td><td>{item}</td>"
            f"<td>{_rich(it.get('status'), base)}</td><td>{_t(it.get('reported_by'))}</td><td>{_t(it.get('owner'))}</td>"
            f"<td>{_ops_tickets(it.get('tickets'), base)}</td><td>{_link(src.get('label'), src.get('url'))}</td></tr>"
        )
    return (
        f"<p>{len(items)} items from the Daily Ops Standup ({counts}).</p>"
        "<table><tr><th>Date</th><th>Type</th><th>Item</th><th>Status / next step</th><th>Update by</th>"
        "<th>Owner</th><th>Jira tickets</th><th>Source</th></tr>"
        + "".join(rows) + "</table>"
    )


def _top(title: str, body: str, fold: bool = False) -> str:
    """Top-level report section that the Collapse all / Expand buttons also control.
    fold=True: "Expand Proj+SubItems" closes it (the project view hides the overview and the gap list)."""
    return f'<details class="top{" fold" if fold else ""}" open><summary class="top"><h2>{escape(title)}</h2></summary>{body}</details>'


def _people(p: dict) -> str:
    return (
        f"Project Manager: <b>{_t(p.get('project_manager'))}</b> &nbsp;|&nbsp; "
        f"Technical Lead: <b>{_t(p.get('technical_lead'))}</b>"
    )


def _project(p: dict, base: str = JIRA_BROWSE) -> str:
    links = p.get("links") or {}
    return (
        f'<details class="card" id="{_anchor(p.get("name"))}" open>'
        f'<summary class="card-h"><div><h3>{_t(p.get("name"))}</h3><div class="meta">{_people(p)}</div></div>'
        f"{_pill(p)}</summary>"
        f"{_sec(1, 'Project updates (summary)', _summary(p, base))}"
        f"{_sec(2, 'Jira task updates needed', _jira_updates(p, base))}"
        f"{_sec(3, 'Project sources', _sources(p))}"
        f"{_sec(4, 'Project meeting chats', _link_list(links.get('teams')))}"
        f"{_sec(5, 'Project SharePoint folder', _link_list(links.get('sharepoint')))}"
        f"{_sec(6, 'Project Confluence page', _link_list(links.get('confluence')))}"
        f"{_sec(7, 'Jira tickets for this project', _tickets(p, base))}</details>"
    )


EXTRA_CSS = """
p.tools{margin:20px 0 0}
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
.card-h{display:flex;justify-content:space-between;align-items:center;gap:12px;list-style:none;cursor:pointer}
.card-h::-webkit-details-marker,summary.sec::-webkit-details-marker{display:none}
.card-h::before{content:'\\25BE';color:var(--forest);font-size:18px}.card:not([open])>.card-h::before{content:'\\25B8'}
.card-h>div{flex:1}
summary.top{list-style:none;display:flex;align-items:center;gap:8px;cursor:pointer}
summary.top::-webkit-details-marker{display:none}
summary.top::before{content:'\\25BE';color:var(--forest);font-size:18px}details.top:not([open])>summary.top::before{content:'\\25B8'}
.card h3{font-size:22px}.meta{margin:.35rem 0 0;font-size:13px;font-weight:400}
.cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:24px}
summary.sec{list-style:none;cursor:pointer;display:flex;align-items:center;gap:8px;margin:1.4rem 0 .4rem;font-size:15px;border-bottom:1px solid var(--forest);padding-bottom:4px}
summary.sec span{background:var(--forest);color:var(--spearmint);border-radius:50%;width:22px;height:22px;display:inline-flex;align-items:center;justify-content:center;font-size:12px}
.lbl{font-weight:600;margin:.6rem 0 .2rem}.refs{font-size:13px}
table.tix tr.done td{opacity:.6}
ul{margin:.25rem 0;padding-left:1.2rem}
details{margin:.5rem 0}summary{cursor:pointer;color:var(--forest);font-weight:600}
@media print{header.top{-webkit-print-color-adjust:exact;print-color-adjust:exact}}
"""


REPORT_TZ = "America/New_York"


def _local(value):
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    tz = ZoneInfo(REPORT_TZ)
    return dt.replace(tzinfo=tz) if dt.tzinfo is None else dt.astimezone(tz)


def _range(window) -> str:
    """'Analysis period: yyyy.mm.dd - yyyy.mm.dd hh:mm EDT'; the zone label is EST or EDT as in force."""
    try:
        start, end = _local(window["from"]), _local(window["to"])
    except (TypeError, KeyError):
        start = end = None
    if not start or not end:
        return f"Analysis period: {NA}"
    return f"Analysis period: {start:%Y.%m.%d} - {end:%Y.%m.%d %H:%M} {end.tzname()}"


def _stamp(value) -> str:
    """'yyyy.mm.dd hh:mm EDT' (America/New_York, 24h) for a timestamp."""
    dt = _local(value)
    return f"{dt:%Y.%m.%d %H:%M} {dt.tzname()}" if dt else NA


LINK_ATTRS = ' target="_blank" rel="noopener"'


def _shrink(html: str, base: str) -> str:
    """Compact build: drop repeated link attributes and Jira hrefs; the page script restores them on load."""
    pattern = (
        r'<a href="' + re.escape(escape(base, quote=True)) + r'([A-Z][A-Z0-9]+-\d+)"'
        + re.escape(LINK_ATTRS) + r'>\1</a>'
    )
    html = re.sub(pattern, r'<a class="j">\1</a>', html)
    # an apostrophe needs no escaping in text or inside double-quoted attributes; the entity form is easy to
    # "correct" when the file is pasted into the upload call
    html = html.replace(LINK_ATTRS, "").replace("&#x27;", "'")
    # plain-ASCII look-alikes for characters that get altered in transit (no-break space, en dash)
    html = html.replace("&nbsp;", " ").replace("–", "-")
    return _unentity(html)


def _unentity(html: str) -> str:
    """Write & and " as plain characters (text) and & (inside tags) instead of entities, so the file survives
    being pasted into the upload call unchanged. Kept only when the parsed text is identical."""
    parts = re.split(r"(<[^>]*>)", html)
    out = []
    for part in parts:
        if part.startswith("<") and part.endswith(">"):
            out.append(part.replace("&amp;", "&"))
        else:
            out.append(part.replace("&amp;", "&").replace("&quot;", '"'))
    plain = "".join(out)
    return plain if unescape(plain) == unescape(html) else html


def render(data: dict, title: str, compact: bool = False) -> str:
    html = _render(data, title, compact)
    return _shrink(html, str(data.get("jira_base_url") or JIRA_BROWSE)) if compact else html


def _render(data: dict, title: str, compact: bool) -> str:
    base = str(data.get("jira_base_url") or JIRA_BROWSE)
    projects = data.get("projects", [])
    gaps = data.get("gaps", [])
    non_project = data.get("non_project") or []
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
        + _card("Daily Ops items", len(non_project), "health, incidents, problems, issues")
        + _card("Data gaps", len(gaps), "see end of report")
    )
    glance = "".join(
        f'<tr><td><a href="#{_anchor(p.get("name"))}">{_t(p.get("name"))}</a></td><td>{_pill(p)}</td>'
        f'<td>{_rich(p.get("progress"), base)}</td><td>{_rich(p.get("timeline"), base)}</td>'
        f'<td>{_rich((p.get("risks") or [None])[0], base)}</td></tr>'
        for p in projects
    )
    gap_html = (
        _top("Data gaps", f"<p>{len(gaps)} gaps in this run</p>" + _ul([f"<li>{_rich(g, base)}</li>" for g in gaps]), fold=True)
        if gaps else ""
    )
    return (
        brand.head(title, EXTRA_CSS, fonts=not compact)
        + "<body>"
        + brand.banner("I&O PROJECT STATUS REPORT", f"Generated: {_stamp(data.get('generated_at'))}",
                       _range(data.get("window")), compact=compact, note_html=brand.header_links(),
                       subtitle_last=True)
        + "<main class='wrap'>"
        f"<h2>Summary</h2><div class='kpis'>{kpis}</div>"
        "<p class='tools'>"
        + _tool("collapse-all", "Collapse all", ICON_COLLAPSE)
        + _tool("expand-all", "Expand all", ICON_EXPAND)
        + _tool("expand-projects", "Expand Proj+SubItems", ICON_TREE)
        + "</p>"
        + _top("Projects at a glance",
               "<table><tr><th>Project</th><th>Status</th><th>Progress</th><th>Timeline</th><th>Top risk</th></tr>"
               f"{glance}</table>", fold=True)
        + "<h2>Project status</h2>"
        f"{''.join(_project(p, base) for p in projects)}"
        + _top(OPS_TITLE, _non_project(non_project, base), fold=True)
        + _top("Sprint status", _sprint(sprint))
        + gap_html
        + brand.footer()
        + "</main>" + brand.foot(base)
    )


def build(data_path: Path, compact: bool = False) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = spend._out_path(data_path.parent, f"{run_id}.html", compact)
    out.write_bytes(render(data, run_id, compact).encode("utf-8"))  # LF endings: bytes match what is uploaded
    return out
