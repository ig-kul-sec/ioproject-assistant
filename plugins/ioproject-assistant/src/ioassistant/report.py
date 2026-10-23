"""Render the IO Project Assistant HTML status report from merged run data."""
from __future__ import annotations

import json
import re
from datetime import date, datetime, timedelta
from urllib.parse import quote
from zoneinfo import ZoneInfo
from html import escape, unescape
from pathlib import Path

from . import brand, orgteams, spend

NA = "n/a"


def _t(value) -> str:
    return escape(str(value)) if value not in (None, "") else NA


ISO_DATE = re.compile(r"(?<![\w/.-])\d{4}-(\d{2})-(\d{2})(?:T[\d:.]+(?:Z|[+-]\d{2}:?\d{2})?)?(?![\w-])")
MD_DATE = re.compile(r"(?<![\w/.:-])(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])(?![\w-])")
TICKET_IN_TEXT = re.compile(r"(?<![\w/-])((?:IOSP|RM|COR)-\d+)(?![\w-])")
# an already linked key followed by bare numbers: "IOSP-1004/1005", "IOSP-1004, 1005", "IOSP-1004 and 1005"
LINKED_SHORT = re.compile(r">((?:IOSP|RM|COR)-)(\d+)</a>((?:\s*(?:/|,|\band\b)\s*\d+(?![\w-]))+)")


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
    base = base or JIRA_BROWSE
    text = TICKET_IN_TEXT.sub(lambda m: _ticket_link(m.group(1), base), text)
    return LINKED_SHORT.sub(lambda m: _short_tickets(m, base), text)


def _short_tickets(m, base: str) -> str:
    """'IOSP-1004/1005' shorthand: link each extra number as a key with the same prefix (and digit count)."""
    prefix, first, rest = m.groups()

    def one(n):
        num = n.group(2)
        return n.group(1) + (_ticket_link(prefix + num, base) if len(num) == len(first) else num)

    return f">{prefix}{first}</a>" + re.sub(r"(\s*(?:/|,|\band\b)\s*)(\d+)(?![\w-])", one, rest)


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
COMPACT_TICKET_CAP = 20  # active tickets per project in the upload copy (keeps it under about 100 KB)
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


def _sprint_url(name) -> str:
    """Jira issue navigator listing the tickets of a sprint, newest update first."""
    jql = f'sprint = "{name}" order by updated DESC'
    return f"{JIRA_BROWSE.rsplit('browse/', 1)[0]}issues/?jql={quote(jql)}"


def _sprint_changes(sprint: dict) -> str:
    """Tickets added to or removed from the sprint on its 2nd day or later, with date and who did it."""
    changes = sprint.get("changes") or []
    try:
        day2 = _md((date.fromisoformat(sprint["start"]) + timedelta(days=1)).isoformat())
    except (KeyError, TypeError, ValueError):
        day2 = NA
    added = sum(1 for c in changes if c.get("action") == "added")
    if not changes:
        return f"<p>No tickets were added to or removed from the sprint from day 2 ({day2}) onward.</p>"
    rows = "".join(
        f"<tr>{_date_td(c.get('date'))}<td>{_t(str(c.get('action') or '').capitalize())}</td>"
        f"<td>{_link(c.get('key'), c.get('url'))}</td><td>{_t(c.get('name'))}</td><td>{_t(c.get('status'))}</td>"
        f"<td>{_t(c.get('assignee'))}</td><td>{_t(c.get('by'))}</td><td>{_t(c.get('other_sprint'))}</td></tr>"
        for c in changes
    )
    return (
        f"<p>From day 2 of the sprint ({day2}) onward: {added} added, {len(changes) - added} removed.</p>"
        "<table><tr><th>Date</th><th>Action</th><th>Ticket</th><th>Ticket name</th><th>Status</th>"
        "<th>Responsible</th><th>Done by</th><th>Other sprint</th></tr>" + rows + "</table>"
        "<p class='note'>From the Jira change history of the Sprint field. A ticket moved between sprints shows as "
        "removed from one and added to the other; 'Other sprint' is where it came from or went to.</p>"
    )


STATUS_ORDER = ("backlog", "to do", "in progress", "qa", "on hold", "unassigned", "done")  # workflow order


def _status_rank(status) -> int:
    """Position of a Jira status in the workflow order; statuses not listed (Rejected, ...) sort after Done."""
    name = re.sub(r"[\s_-]+", " ", str(status or "").strip().lower()).replace("todo", "to do")
    return STATUS_ORDER.index(name) if name in STATUS_ORDER else len(STATUS_ORDER)


def _sprint_body(sprint: dict) -> str:
    dur = _days(sprint.get("start"), sprint.get("end"))
    tickets = sorted(sprint.get("tickets", []), key=lambda t: _status_rank(t.get("status")))  # stable: Jira order within a status
    done = sum(1 for t in tickets if any(w in str(t.get("status") or "").lower() for w in DONE_WORDS))
    pct = f"{round(100 * done / len(tickets))}%" if tickets else NA
    rows = "".join(
        f"<tr><td>{_link(t.get('key'), t.get('url'))}</td><td>{_t(t.get('name') or t.get('summary'))}</td>"
        f"<td>{_t(t.get('status'))}</td><td>{_t(t.get('assignee'))}</td>{_date_td(t.get('due'))}</tr>"
        for t in tickets
    )
    return (
        (f"<p>{_link('JIRA Tickets Link: Sprint ' + str(sprint['name']), _sprint_url(sprint['name']))}</p>"
         if sprint.get("name") else "")
        + f"<p><b>{_t(sprint.get('name'))}</b>: {_t(_md(sprint.get('start')))} to {_t(_md(sprint.get('end')))}"
        f" ({dur if dur is not None else NA} days). {done} of {len(tickets)} tickets done ({pct}).</p>"
        f"<details class=\"sub\"><summary>All {len(tickets)} sprint tickets</summary>"
        "<table><tr><th>Ticket</th><th>Ticket name</th><th>Status</th><th>Responsible</th><th>Due</th></tr>"
        f"{rows}</table></details>"
    )


def _bars(rows: list, total: bool = False, stacked: bool = False) -> str:
    """Horizontal bar chart in CSS. rows: (label, value) or, when stacked, (label, done, open).
    total=True adds a closing "Total" row (no bar) with the sum of all rows."""
    top = max((sum(r[1:]) for r in rows), default=0) or 1
    out = []
    for r in rows:
        label, vals = r[0], r[1:]
        segs = "".join(
            f"<i class='seg{' open' if stacked and k else ''}' style='width:{100 * v / top:.1f}%'></i>"
            for k, v in enumerate(vals) if v
        )
        out.append(f"<div class='bar'><span class='bl'>{_t(label)}</span><span class='bt'>{segs}</span>"
                   f"<span class='bv'>{sum(vals)}</span></div>")
    if total:
        out.append(f"<div class='bar total'><span class='bl'>Total</span><span class='bt'></span>"
                   f"<span class='bv'>{sum(sum(r[1:]) for r in rows)}</span></div>")
    return "<div class='bars'>" + "".join(out) + "</div>"


UNASSIGNED = "Unassigned"


def _done_open(tickets: list) -> tuple:
    """(done, not done) ticket counts."""
    done = sum(1 for t in tickets if _is_done(t))
    return done, len(tickets) - done


NOTES = {orgteams.OTHER: "reporting to other managers", UNASSIGNED: "no assignee"}


def _team_workload(tickets: list, roster: dict) -> str:
    """Tickets per team (reporting lines from Ardoq): stacked done/not-done bars plus a workload table."""
    index = orgteams.team_index(roster)
    teams = roster.get("teams", [])
    stats = {t["name"]: [0, 0] for t in teams}
    stats[orgteams.OTHER] = [0, 0]
    stats[UNASSIGNED] = [0, 0]
    others: dict = {}
    for t in tickets:
        who = t.get("assignee")
        team = orgteams.team_of(index, who) if who else UNASSIGNED
        stats[team][0 if _is_done(t) else 1] += 1
        if team == orgteams.OTHER:
            others[who] = others.get(who, 0) + 1
    info = {t["name"]: t for t in teams}
    order = [t["name"] for t in teams] + [orgteams.OTHER, UNASSIGNED]

    def label(name: str) -> str:
        return f"{name} ({info[name]['manager']})" if name in info and info[name].get("manager") else name

    rows = "".join(
        f"<tr><td>{_t(name)}</td><td>{_t(info[name].get('manager')) if name in info else NOTES.get(name, NA)}</td>"
        + (f"<td>{orgteams.headcount(info[name])}</td>" if name in info else f"<td>{NA}</td>")
        + f"<td>{sum(stats[name])}</td><td>{stats[name][0]}</td><td>{stats[name][1]}</td>"
        + (f"<td>{sum(stats[name]) / orgteams.headcount(info[name]):.1f}</td>" if name in info else f"<td>{NA}</td>")
        + "</tr>"
        for name in order
    ) + (
        f"<tr class='total'><td><b>Total</b></td><td></td><td>{sum(orgteams.headcount(t) for t in teams)}</td>"
        f"<td><b>{sum(sum(s) for s in stats.values())}</b></td><td><b>{sum(s[0] for s in stats.values())}</b></td>"
        f"<td><b>{sum(s[1] for s in stats.values())}</b></td><td>{NA}</td></tr>"
    )
    other_note = (" Other: " + ", ".join(f"{escape(n)} ({c})" for n, c in sorted(others.items(), key=lambda kv: (-kv[1], kv[0])))
                  + ".") if others else ""
    asof = roster.get("as_of")
    return (
        "<p class='legend'><i class='seg'></i> done <i class='seg open'></i> not done</p>"
        + _bars([(label(n), *stats[n]) for n in order], total=True, stacked=True)
        + "<table><tr><th>Team</th><th>Manager</th><th>People</th><th>Tickets</th><th>Done</th><th>Not done</th>"
          f"<th>Tickets per person</th></tr>{rows}</table>"
        + f"<p class='note'>Teams follow the reporting lines in Ardoq (Organization structure), "
          f"{'live for this run' if roster.get('live') else 'static snapshot dated ' + escape(str(asof or NA))}; "
          f"the manager counts as part of the team. Other = assignees reporting to other managers; "
          f"Unassigned = tickets with no assignee, so the total matches all sprint tickets.{other_note}</p>"
    )


def _idle_employees(tickets: list, roster: dict) -> str:
    """Per team, the employees (Ardoq roster members) with no ticket in this sprint, whatever its status."""
    idle = orgteams.idle(roster, [t.get("assignee") for t in tickets])
    info = {t["name"]: t for t in roster.get("teams", [])}
    rows = "".join(
        f"<tr><td>{_t(name)}</td><td>{_t(info[name].get('manager'))}</td>"
        f"<td>{len(people)} of {len(info[name].get('members', []))}</td>"
        f"<td>{', '.join(escape(n) for n in people) or 'everyone has a ticket'}</td></tr>"
        for name, people in idle.items()
    )
    total = sum(len(p) for p in idle.values())
    return (f"<p>{total} employees have no ticket in this sprint (Done tickets count as assigned).</p>"
            f"<table><tr><th>Team</th><th>Manager</th><th>Without tickets</th><th>Employees</th></tr>{rows}</table>"
            "<p class='note'>Based on the Ardoq roster; managers are not counted as employees. "
            "Tickets are matched by name or email.</p>")


def _sprint_charts(sprint: dict, roster: dict | None = None) -> str:
    """Resource-assignment charts for one sprint: headline counts, tickets by status, by team, load per assignee."""
    tickets = sprint.get("tickets", [])
    if not tickets:
        return ""
    roster = roster if roster is not None else orgteams.load()
    team_idx = orgteams.team_index(roster)
    by_status: dict = {}
    for t in tickets:
        k = str(t.get("status") or "n/a")
        by_status[k] = by_status.get(k, 0) + 1
    people: dict = {}
    for t in tickets:
        who = t.get("assignee")
        if who:
            done_open = people.setdefault(who, [0, 0])
            done_open[0 if _is_done(t) else 1] += 1
    unassigned = sum(1 for t in tickets if not t.get("assignee"))
    done = sum(1 for t in tickets if _is_done(t))
    assigned = len(tickets) - unassigned
    ranked = sorted(people.items(), key=lambda kv: (-sum(kv[1]), kv[0]))
    busiest = ranked[0] if ranked else None
    kpis = (
        _card("Sprint tickets", len(tickets), f"{done} done")
        + _card("People with tickets", len(people), f"{assigned} tickets assigned")
        + _card("Unassigned tickets", unassigned, "no responsible person")
        + _card("Highest load", sum(busiest[1]) if busiest else NA, escape(busiest[0]) if busiest else "")
    )
    status_rows = sorted(by_status.items(), key=lambda kv: (_status_rank(kv[0]), kv[0]))
    return (
        _sec(1, "Sprint at a glance", f"<div class='kpis'>{kpis}</div>")
        + _sec(2, "Tickets by status", _bars(status_rows, total=True))
        + _sec(3, "Tickets by team", _team_workload(tickets, roster))
        + _sec(4, "Employees without tickets assigned in sprint", _idle_employees(tickets, roster))
        + _sec(5, "Tickets by employee",
               "<p class='legend'><i class='seg'></i> done <i class='seg open'></i> not done"
               f" &middot; {len(people)} employees account for {assigned} of {len(tickets)} tickets"
               + (f" &middot; {unassigned} unassigned" if unassigned else "") + "</p>"
               + _bars([(f"{n} ({orgteams.team_of(team_idx, n)})", d, o) for n, (d, o) in ranked]
                       + ([(UNASSIGNED, *_done_open([t for t in tickets if not t.get("assignee")]))] if unassigned else []),
                       total=True, stacked=True)
               + "<p class='note'>Counts tickets, not story points or effort.</p>")
        + (_sec(6, "Tickets added or removed from the sprint (day 2 onward)", _sprint_changes(sprint))
           if sprint.get("changes") is not None else "")
    )


def _sprint(sprint: dict, past: list[dict] | None = None) -> str:
    """Collapsible subsections: each past sprint still active (oldest first), then the current one."""
    subs = [(f"Past sprint {s['name']} (not closed yet)" if s.get("name") else "Past sprint (not closed yet)", s)
            for s in past or []]
    subs += [(f"Current sprint {sprint['name']}" if sprint.get("name") else "Current sprint", sprint)] if sprint else []
    if not subs:
        return "<p>No sprint data.</p>"
    return "".join(_sec(i, title, _sprint_body(s)) for i, (title, s) in enumerate(subs, 1))


def _sprint_management(sprint: dict, past: list[dict] | None = None, roster: dict | None = None) -> str:
    """Sprint management tab: board link, then the "Sprint charts" and "JIRA tickets" sections (each foldable)."""
    board = _link("JIRA ScrumBoard Link", brand.JIRA_BOARD_URL)
    charts = _sprint_charts(sprint or {}, roster) or "<p>No sprint tickets.</p>"
    return (f"<p>{board}</p>" + _top("Sprint charts", charts, ident="sprint-charts")
            + _top("JIRA tickets", _sprint(sprint, past), ident="sprint"))


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
            f"<td>{_t(c.get('type'))}</td><td>{_rich(c.get('detail'), base)}</td><td>{_rich(c.get('reason'), base)}</td></tr>"
            for c in change
        )
        html += (
            "<p class='lbl'>Existing tickets to change</p>"
            "<table><tr><th>Ticket</th><th>Ticket name</th><th>Change</th><th>What to do</th><th>Reason/Comment</th></tr>" + rows + "</table>"
        )
    if create:
        rows = "".join(
            f"<tr><td>{_rich(c.get('name'), base)}</td><td>{_rich(c.get('description'), base)}</td><td>{_rich(c.get('reason'), base)}</td>"
            f"{_date_td(c.get('start'))}{_date_td(c.get('end'))}<td>{_t(c.get('owner'))}</td></tr>"
            for c in create
        )
        html += (
            "<p class='lbl'>New tickets to create</p>"
            "<table><tr><th>Name</th><th>Description</th><th>Reason/Comment</th><th>Start</th><th>End</th><th>Responsible</th></tr>"
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


def _tickets(p: dict, base: str, compact: bool = False, sprint_of: dict | None = None) -> str:
    ts = sorted(p.get("tickets") or [], key=lambda t: (_is_done(t), not t.get("epic")))
    omitted = 0
    if compact:  # the upload copy must stay small: closed tickets stay in the full local report
        kept = [t for t in ts if not _is_done(t)][:COMPACT_TICKET_CAP]
        omitted, ts = len(ts) - len(kept), kept
    note = (f"<p class='lbl'>{omitted} tickets are left out of this copy (closed or done, or beyond the first "
            f"{COMPACT_TICKET_CAP} active ones); the full list is in the local report.</p>") if omitted else ""
    if not ts:
        return note or f"<p>{NA}</p>"
    rows = "".join(
        f"<tr class=\"{'done' if _is_done(t) else 'active'}\"><td>{_ticket_link(t, base)}</td>"
        f"<td>{_rich(t.get('name') or t.get('summary'), base)}</td><td>{_t(t.get('status'))}</td>"
        f"<td>{_t(t.get('sprint') or (sprint_of or {}).get(str(t.get('key'))))}</td>"
        f"<td>{_t(t.get('assignee'))}</td>{_date_td(t.get('start'))}{_date_td(t.get('end') or t.get('due'))}"
        f"<td>{', '.join(_ticket_link(r, base) for r in t.get('related') or []) or NA}</td></tr>"
        for t in ts
    )
    return (
        "<table class='tix'><tr><th>Ticket #</th><th>Ticket name</th><th>Status</th><th>Sprint</th><th>Responsible</th>"
        f"<th>Start</th><th>End</th><th>Related tickets</th></tr>{rows}</table>" + note
    )


# line icons (brand 6.3: single-weight stroke, rounded, currentColor)
ICON_COLLAPSE = "<path d='M7 4l5 5 5-5'/><path d='M7 20l5-5 5 5'/>"
ICON_EXPAND = "<path d='M7 9l5-5 5 5'/><path d='M7 15l5 5 5-5'/>"
ICON_TREE = "<path d='M3 6h18'/><path d='M7 12h14'/><path d='M11 18h10'/>"


def _tool(ident: str, label: str, icon: str) -> str:
    return (f"<button class='tool' id='{ident}'><svg viewBox='0 0 24 24' aria-hidden='true'>{icon}</svg>"
            f"{escape(label)}</button>")


def _tabs(items: list) -> str:
    """Tab bar under the Collapse/Expand buttons; the page script shows one panel at a time (all show without it)."""
    return "<div class='tabs' role='tablist'>" + "".join(
        f"<button role='tab' data-tab='{ident}'>{escape(label)}</button>" for ident, label in items
    ) + "</div>"


def _panel(ident: str, body: str) -> str:
    return f"<section class='tabpanel' id='{ident}' role='tabpanel'>{body}</section>"


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


def _top(title: str, body: str, fold: bool = False, ident: str = "") -> str:
    """Top-level report section that the Collapse all / Expand buttons also control.
    fold=True: "Expand Proj+SubItems" closes it (the project view hides the overview and the gap list).
    ident is the anchor the contents rail on the left links to."""
    anchor = f' id="{ident}"' if ident else ""
    return f'<details class="top{" fold" if fold else ""}"{anchor} open><summary class="top"><h2>{escape(title)}</h2></summary>{body}</details>'


def _contents(projects: list, has_gaps: bool) -> str:
    """Sticky contents rail on the left (like the guide): section links, then one link per project with its status dot."""
    def group(text: str) -> str:
        return f"<div class='grp'>{escape(text)}</div>"

    def link(href: str, text: str, dot: str = "") -> str:
        mark = f"<i class='dot {dot}'></i>" if dot else ""
        return f"<a href='#{href}'>{mark}{escape(text)}</a>"

    return (
        "<nav class='toc' aria-label='Contents'>"
        + link("top", "Go to the top")
        + group("Overview") + link("summary", "Summary") + link("glance", "Projects at a glance")
        + group("Project status")
        + "".join(link(_anchor(p.get("name")), str(p.get("name") or NA), _rag(p)[1]) for p in projects)
        + group("More")
        + link("ops", "Daily Ops health and incidents") + link("sprint-charts", "Sprint charts") + link("sprint", "JIRA tickets")
        + (link("gaps", "Data gaps") if has_gaps else "")
        + "</nav>"
    )


def _people(p: dict) -> str:
    return (
        f"Project Manager: <b>{_t(p.get('project_manager'))}</b> &nbsp;|&nbsp; "
        f"Technical Lead: <b>{_t(p.get('technical_lead'))}</b>"
    )


def _project(p: dict, base: str = JIRA_BROWSE, compact: bool = False, sprint_of: dict | None = None) -> str:
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
        f"{_sec(7, 'Jira tickets for this project', _tickets(p, base, compact, sprint_of))}</details>"
    )


EXTRA_CSS = """
.wrap{max-width:1360px}
.layout{display:grid;grid-template-columns:220px minmax(0,1fr);gap:48px;padding-top:32px;padding-bottom:48px}
.layout>main{min-width:0}
.layout>main>h2:first-child{margin-top:0}
nav.toc{position:sticky;top:16px;align-self:start;max-height:calc(100vh - 32px);overflow-y:auto;font-size:14px;display:grid;gap:2px;padding-top:6px}
nav.toc a{text-decoration:none;color:var(--off-black);opacity:.75;padding:3px 0;display:flex;align-items:center;gap:8px}
nav.toc a:hover{opacity:1;background:none;color:var(--forest);text-decoration:underline;text-decoration-color:var(--spearmint)}
nav.toc .grp{margin-top:14px;font-weight:700;color:var(--forest);font-family:'Urbanist',Arial,sans-serif}
nav.toc .grp:first-child{margin-top:0}
nav.toc .dot{flex:none;width:10px;height:10px;border-radius:50%;border:1px solid var(--off-black)}
nav.toc .dot.ok{background:var(--spearmint);border-color:var(--forest)}
nav.toc .dot.risk{background:var(--scout)}
nav.toc .dot.off{background:var(--coral)}
html{scroll-behavior:smooth}
@media (max-width:900px){.layout{grid-template-columns:minmax(0,1fr)}nav.toc{display:none}}
@media print{nav.toc{display:none}.layout{display:block}}
p.tools{margin:20px 0 0}
.tabs{display:flex;flex-wrap:wrap;gap:6px;margin:24px 0 0;padding-top:4px;border-bottom:4px solid var(--forest)}
.tabs button{font:700 17px 'Urbanist',Arial,sans-serif;background:var(--spearmint);color:var(--forest);border:2px solid var(--forest);border-bottom:0;border-radius:10px 10px 0 0;padding:12px 28px;cursor:pointer;box-shadow:0 -1px 3px rgba(0,0,0,.15)}
.tabs button:hover{background:var(--forest);color:var(--spearmint)}
.tabs button.on{background:var(--forest);color:var(--off-white);padding-bottom:14px;margin-bottom:-4px;box-shadow:inset 0 4px 0 var(--spearmint)}
.bars{display:grid;gap:6px;margin:8px 0 4px}
.bar{display:grid;grid-template-columns:minmax(120px,200px) 1fr 32px;align-items:center;gap:10px}
.bl{font-weight:600;text-align:right;overflow:hidden;text-overflow:ellipsis;white-space:nowrap}
.bt{display:flex;height:20px;background:rgba(1,82,88,.08);border-radius:4px;overflow:hidden}
.seg{display:inline-block;height:100%;background:var(--forest)}.seg.open{background:var(--spearmint)}
.bv{font-weight:700;color:var(--forest)}
.bar.total{border-top:1px solid var(--forest);padding-top:4px}.bar.total .bt{background:none}
.legend{font-size:13px;margin:6px 0}.legend .seg{width:12px;height:12px;vertical-align:-1px;margin-left:8px;border-radius:2px}
.note{font-size:12px;opacity:.8}
body.tabbed .tabpanel{display:none}body.tabbed .tabpanel.on{display:block}
@media print{body.tabbed .tabpanel{display:block}.tabs{display:none}}
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
    html = html.replace("&nbsp;", " ").replace("–", "-").replace("·", "&middot;")
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
    roster = orgteams.load(data)
    gaps = list(data.get("gaps", []))
    if (data.get("sprint") or {}).get("tickets") and not roster["live"]:
        gaps.append(f"Ardoq: team roster is the static snapshot dated {roster.get('as_of') or NA}; "
                    "Ardoq was not connected for this run (sign in with /mcp to refresh it).")
    non_project = data.get("non_project") or []
    attention = sum(1 for p in projects if _rag(p)[1] in ("risk", "off"))
    jira_todo = sum(
        len((p.get("jira_updates") or {}).get("change") or []) + len((p.get("jira_updates") or {}).get("create") or [])
        for p in projects
    )
    sprint = data.get("sprint") or {}
    tickets = sprint.get("tickets", [])
    past = [s for s in data.get("past_sprints") or [data.get("past_sprint")] if s]
    sprint_of = {str(t.get("key")): s.get("name") for s in past for t in s.get("tickets") or [] if s.get("name")}
    sprint_of.update({str(t.get("key")): sprint.get("name") for t in tickets if sprint.get("name")})  # current wins
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
        _top("Data gaps", f"<p>{len(gaps)} gaps in this run</p>" + _ul([f"<li>{_rich(g, base)}</li>" for g in gaps]),
             fold=True, ident="gaps")
        if gaps else ""
    )
    return (
        brand.head(title, EXTRA_CSS, fonts=not compact)
        + "<body id='top'>"
        + brand.banner("I&O PROJECT STATUS REPORT", f"Generated: {_stamp(data.get('generated_at'))}",
                       _range(data.get("window")), compact=compact, note_html=brand.header_links(),
                       subtitle_last=True, dev=brand.is_dev(title))
        + "<div class='wrap layout'>"
        + _contents(projects, bool(gaps))
        + "<main>"
        f"<h2 id='summary'>Summary</h2><div class='kpis'>{kpis}</div>"
        "<p class='tools'>"
        + _tool("collapse-all", "Collapse all", ICON_COLLAPSE)
        + _tool("expand-all", "Expand all", ICON_EXPAND)
        + _tool("expand-projects", "Expand Proj+SubItems", ICON_TREE)
        + "</p>"
        + _tabs([("tab-projects", "Projects"), ("tab-ops", "Operations"), ("tab-sprint", "Sprint management")]
                + ([("tab-gaps", "Data gaps")] if gaps else []))
        + _panel("tab-projects",
                 _top("Projects at a glance",
                      "<table><tr><th>Project</th><th>Status</th><th>Progress</th><th>Timeline</th><th>Top risk</th></tr>"
                      f"{glance}</table>", fold=True, ident="glance")
                 + "<h2>Project status</h2>"
                 f"{''.join(_project(p, base, compact, sprint_of) for p in projects)}")
        + _panel("tab-ops", _top(OPS_TITLE, _non_project(non_project, base), fold=True, ident="ops"))
        + _panel("tab-sprint", _sprint_management(sprint, past, roster))
        + (_panel("tab-gaps", gap_html) if gaps else "")
        + brand.footer()
        + "</main></div>" + brand.foot(base)
    )


def build(data_path: Path, compact: bool = False) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = spend._out_path(data_path.parent, f"{run_id}.html", compact)
    out.write_bytes(render(data, run_id, compact).encode("utf-8"))  # LF endings: bytes match what is uploaded
    return out
