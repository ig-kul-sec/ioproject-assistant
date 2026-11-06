"""IO Projects Leadership Updates: a digest of the main reports for a period, the leadership report that sets the
roadmap deck's previous information beside a proposal for the new statuses, and the Outlook / Confluence bodies.

Standard library only. The digest (`collect`) is deterministic; the proposals are written by the leadership
orchestrator agent into `data.json` (schema: skills/run-leadership-updates/SKILL.md) and rendered here.
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timedelta
from html import escape
from pathlib import Path
from zoneinfo import ZoneInfo

from . import brand, emaildraft, report, spend

RUN_PREFIX = "IOProjectLeadershipUpdates"
TZ = ZoneInfo("America/New_York")
# main report runs: PROD runs, and DEV runs (only read when the leadership run is a DEV run too)
RUN_RE = re.compile(r"^(?:DEV_)?IOProjectAssistantReport_(\d{8})_(\d{4})$")
ALIASES_PATH = Path(__file__).resolve().parents[2] / "config" / "leadership-projects.json"
LINK_KINDS = {"teams": "chats", "sharepoint": "sharepoint", "confluence": "confluence", "jira": "jira"}
LINK_CAP = 15  # links per kind in the digest (newest first)
BLOCKS = [
    ("accomplishments", "Accomplishments"), ("whats_next", "What's next"), ("issues", "Issues"),
    ("risks", "Risks"), ("dependencies", "Dependencies"), ("milestones", "Milestones"),
]
RAGS = (("schedule", "Schedule"), ("scope", "Scope"), ("cost", "Cost"))
STATUSES = {
    "on track": ("On track", "ok"), "at risk": ("At risk", "risk"), "off track": ("Off track", "off"),
    "paused": ("Paused", "pause"),
}
RAG_CLASS = {"g": ("Green", "ok"), "y": ("Yellow", "risk"), "r": ("Red", "off")}
NA = report.NA


# --- names ---------------------------------------------------------------------------------------------------------

def is_leadership(run_id: str) -> bool:
    """True for 'IOProjectLeadershipUpdates_<yyyymmdd>_<hhmm>' and its DEV_ twin."""
    name = str(run_id)
    return name[len(brand.DEV_PREFIX):].startswith(RUN_PREFIX) if brand.is_dev(name) else name.startswith(RUN_PREFIX)


def _run_time(run_id: str):
    m = RUN_RE.match(run_id)
    if not m:
        return None
    try:
        return datetime.strptime(m.group(1) + m.group(2), "%Y%m%d%H%M").replace(tzinfo=TZ)
    except ValueError:
        return None


def _norm_text(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip().lower()


def _text(item) -> str:
    return str(item.get("text") if isinstance(item, dict) else item or "").strip()


# --- digest of the main reports ------------------------------------------------------------------------------------

def load_aliases(path: Path = ALIASES_PATH) -> list[dict]:
    """Deck project names and the words that identify the same project in the main reports."""
    return json.loads(path.read_text(encoding="utf-8"))["projects"]


def match_project(name, aliases: list[dict]):
    """Deck project name for a main-report project name (first alias word found in it), else None."""
    low = str(name or "").lower()
    for alias in aliases:
        if any(word.lower() in low for word in alias.get("match", [])):
            return alias["name"]
    return None


def find_runs(output_dir: Path, start: datetime, end: datetime, dev: bool = False) -> list[dict]:
    """Main report runs (folder with data.json and the rendered html) made between start and end, oldest first."""
    patterns = ["IOProjectAssistantReport_*"] + (["DEV_IOProjectAssistantReport_*"] if dev else [])
    runs = []
    for pattern in patterns:
        for folder in sorted(Path(output_dir).glob(pattern)):
            when = _run_time(folder.name)
            data_file = folder / "data.json"
            if when is None or not start <= when <= end or not data_file.is_file() or not (folder / f"{folder.name}.html").is_file():
                continue
            runs.append({"run_id": folder.name, "when": when, "data": json.loads(data_file.read_text(encoding="utf-8"))})
    return sorted(runs, key=lambda r: r["when"])


def _empty(alias: dict) -> dict:
    return {"deck_name": alias["name"], "report_names": [], "found": False, "latest": {}, "status_history": [],
            "updates": [], "risks": [], "action_items": [], "jira_changes": [],
            "resources": {"epics": [], "chats": [], "sharepoint": [], "confluence": [], "jira": [], "other": []}}


def _absorb(entry: dict, run: dict, p: dict, seen: dict) -> None:
    """Fold one run's project into the digest entry (runs are visited oldest first, so the newest values win)."""
    entry["found"] = True
    if p.get("name") and p["name"] not in entry["report_names"]:
        entry["report_names"].append(p["name"])
    day = run["when"].date().isoformat()
    entry["status_history"].append({"run_id": run["run_id"], "date": day, "status": p.get("status")})
    entry["latest"] = {k: p.get(k) for k in ("status", "project_manager", "technical_lead", "progress", "timeline", "dates")}
    items = p.get("summary") or [{"text": n} for n in (p.get("notes") or [])[:3]]
    for it in items:
        text = _text(it)
        if text and _norm_text(text) not in seen["updates"]:
            seen["updates"].add(_norm_text(text))
            entry["updates"].append({"text": text, "tickets": it.get("tickets", []) if isinstance(it, dict) else [],
                                     "run_id": run["run_id"], "date": day})
    for risk in p.get("risks") or []:
        text = _text(risk)
        if text and _norm_text(text) not in seen["risks"]:
            seen["risks"].add(_norm_text(text))
            entry["risks"].append(text)
    for item in p.get("action_items") or []:
        text = _text(item)
        if text and _norm_text(text) not in seen["actions"]:
            seen["actions"].add(_norm_text(text))
            entry["action_items"].append({"text": text, "owner": item.get("owner") if isinstance(item, dict) else None,
                                          "due": item.get("due") if isinstance(item, dict) else None, "run_id": run["run_id"]})
    entry["jira_changes"] = [
        {k: c.get(k) for k in ("key", "name", "type", "detail")} for c in (p.get("jira_updates") or {}).get("change") or []
    ]  # the newest run's list replaces the older one
    base = str(run["data"].get("jira_base_url") or report.JIRA_BROWSE)
    res = entry["resources"]
    for t in p.get("tickets") or []:
        if t.get("epic") and t.get("key"):
            epic = {"key": t["key"], "url": t.get("url") or base + t["key"], "name": t.get("name") or t.get("summary"),
                    "status": t.get("status"), "end": t.get("end")}
            res["epics"] = [e for e in res["epics"] if e["key"] != epic["key"]] + [epic]
    for kind, links in (p.get("links") or {}).items():
        bucket = res[LINK_KINDS.get(kind, "other")]
        for link in links or []:
            if link.get("url"):
                bucket[:] = [x for x in bucket if x["url"] != link["url"]] + [{"label": link.get("label"), "url": link["url"]}]


def collect(output_dir: Path, start: datetime, end: datetime, aliases: list[dict] | None = None, dev: bool = False) -> dict:
    """Digest of the main reports made in the period, per roadmap-deck project (see ALIASES_PATH)."""
    aliases = aliases if aliases is not None else load_aliases()
    runs = find_runs(output_dir, start, end, dev)
    entries = {a["name"]: _empty(a) for a in aliases}
    seen = {name: {"updates": set(), "risks": set(), "actions": set()} for name in entries}
    unmatched: dict = {}
    for run in runs:
        unmatched = {}  # only the newest report's projects count: older runs name the same work differently
        for p in run["data"].get("projects") or []:
            deck_name = match_project(p.get("name"), aliases)
            if deck_name:
                _absorb(entries[deck_name], run, p, seen[deck_name])
            elif p.get("name"):
                unmatched[p["name"]] = {"name": p["name"], "status": p.get("status"), "run_id": run["run_id"],
                                        "summary": [_text(s) for s in (p.get("summary") or [])[:3]]}
    for entry in entries.values():
        entry["updates"].reverse()  # newest first
        for links in entry["resources"].values():
            links.reverse()
            del links[LINK_CAP:]
    ran = {run["when"].date() for run in runs}
    missing, day = [], start.date()
    while day < end.date():  # the last day is still running, so it is not a gap
        if day.weekday() < 5 and day not in ran:
            missing.append(day.isoformat())
        day += timedelta(days=1)
    newest = runs[-1] if runs else None
    return {
        "period": {"from": start.isoformat(), "to": end.isoformat()},
        "runs": [{"run_id": r["run_id"], "generated_at": r["data"].get("generated_at"), "window": r["data"].get("window"),
                  "url": brand.sharepoint_file_url(r["run_id"] + ".html")} for r in runs],
        "days_without_report": missing,
        "projects": list(entries.values()),
        "unmatched_report_projects": list(unmatched.values()),
        "newest_report_gaps": list((newest["data"].get("gaps") if newest else None) or []),
    }


def collect_to(run_dir: Path, start: datetime, end: datetime) -> Path:
    """Write <run folder>/reports.json; the main reports are looked up next to the run folder (output/)."""
    run_dir.mkdir(parents=True, exist_ok=True)
    digest = collect(run_dir.parent, start, end, dev=brand.is_dev(run_dir.name))
    out = run_dir / "reports.json"
    out.write_text(json.dumps(digest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


# --- the report ----------------------------------------------------------------------------------------------------

def _norm_status(value) -> str:
    return re.sub(r"\s+", " ", re.sub(r"\s*-\s*", " ", str(value or "").strip().lower()))


def _status(value) -> tuple[str, str]:
    return STATUSES.get(_norm_status(value), ("Not rated", "na"))


def _pill(value) -> str:
    label, cls = _status(value)
    return f'<span class="pill {cls}">{label}</span>'


def _chips(state: dict) -> str:
    out = []
    for key, label in RAGS:
        letter = str(state.get(key) or "").strip().lower()[:1]
        name, cls = RAG_CLASS.get(letter, (None, "na"))
        out.append(f'<span class="rag {cls}" title="{label}: {name or "not rated"}">{label} {letter.upper() or NA}</span>')
    return " ".join(out)


def _key(text) -> str:
    return re.sub(r"\W+", " ", str(text or "").lower()).strip()


def _items(state: dict, key: str) -> list[str]:
    value = state.get(key)
    if isinstance(value, str):
        value = [value]
    return [str(v).strip() for v in value or [] if str(v).strip()]


def _block(items: list[str], other: list[str], new: bool) -> str:
    """Bullet list; an item the other side lacks is marked (New on the proposal side, Superseded on the deck side)."""
    if not items:
        return f"<p>{NA}</p>"
    other_keys = {_key(x) for x in other}
    rows = []
    for item in items:
        if _key(item) in other_keys:
            rows.append(f"<li>{report._rich(item)}</li>")
        elif new:
            rows.append(f'<li class="new"><b class="tg">New</b> {report._rich(item)}</li>')
        else:
            rows.append(f'<li class="old"><b class="tg">Superseded</b> {report._rich(item)}</li>')
    return "<ul>" + "".join(rows) + "</ul>"


def _differs(deck: dict, proposal: dict, key: str) -> bool:
    return {_key(x) for x in _items(deck, key)} != {_key(x) for x in _items(proposal, key)}


def _status_changed(p: dict) -> bool:
    deck, prop = p.get("deck") or {}, p.get("proposal") or {}
    if _status(deck.get("status"))[0] != _status(prop.get("status"))[0]:
        return True
    return any(str(deck.get(k) or "").strip().lower()[:1] != str(prop.get(k) or "").strip().lower()[:1] for k, _ in RAGS)


def _updated_blocks(p: dict) -> int:
    deck, prop = p.get("deck") or {}, p.get("proposal") or {}
    return sum(1 for key, _ in BLOCKS if _differs(deck, prop, key))


def _row(label: str, left: str, right: str, changed: bool) -> str:
    tag = '<span class="tag chg">Updated</span>' if changed else '<span class="tag same">No change</span>'
    cls = " chg" if changed else ""
    return (f'<div class="rl">{escape(label)} {tag}</div>'
            f'<div class="cell">{left}</div><div class="cell{cls}">{right}</div>')


def _compare(p: dict) -> str:
    """Left: the roadmap deck as it is now. Right: the proposal for the new statuses."""
    deck, prop = p.get("deck") or {}, p.get("proposal") or {}
    slide = f" (slide {escape(str(p['slide']))})" if p.get("slide") else ""
    rows = [_row("Status", f"{_pill(deck.get('status'))} {_chips(deck)}", f"{_pill(prop.get('status'))} {_chips(prop)}",
                 _status_changed(p))]
    for key, label in BLOCKS:
        left, right = _items(deck, key), _items(prop, key)
        rows.append(_row(label, _block(left, right, False), _block(right, left, True), _differs(deck, prop, key)))
    why = (f"<p class='why'><b>Why:</b> {report._rich(p.get('rationale'))}</p>" if p.get("rationale")
           else "<p class='why'><b>Why:</b> no change proposed: the main reports of the period give no evidence against the deck.</p>")
    return (f'<div class="cmp"><div class="hd">Previous information: roadmap deck{slide}</div>'
            f'<div class="hd new">Proposal: new statuses</div>{"".join(rows)}</div>{why}')


def _source(run_id, date) -> str:
    """'report 11/05 10:08' linked to the main report on SharePoint (plain text when the run id is not a run id)."""
    when = _run_time(str(run_id or ""))
    if not when:
        return escape(report._md(date))
    return report._link(f"report {when:%m/%d %H:%M}", brand.sharepoint_file_url(str(run_id) + ".html"))


def _key_changes(p: dict) -> str:
    items = p.get("key_changes") or []
    if not items:
        return "<p>No updates for this project in the main reports of the period.</p>"
    rows = []
    for it in items:
        it = it if isinstance(it, dict) else {"text": it}
        src = _source(it.get("source"), it.get("date"))
        rows.append(f"<li>{report._rich(it.get('text'))}" + (f' <span class="src">({src})</span>' if src else "") + "</li>")
    return "<ul>" + "".join(rows) + "</ul>"


def _resources(p: dict) -> str:
    res = p.get("resources") or {}
    epics = res.get("epics") or []
    epic_rows = "".join(
        f"<li>{report._ticket_link(e, report.JIRA_BROWSE)}"
        + (f" {report._rich(e.get('name'))}" if e.get("name") else "")
        + (f" <span class='src'>({escape(str(e['status']))})</span>" if e.get("status") else "") + "</li>"
        for e in epics
    )
    # two columns, filled row by row in this order: Jira epics, Confluence, SharePoint, Project chats, Other links
    groups = [f"<div class='rg'><p class='lbl'>Jira {'epics' if len(epics) > 1 else 'epic'}</p>"
              + (f"<ul>{epic_rows}</ul>" if epic_rows else f"<p>{NA}</p>") + "</div>"]
    for key, label in (("confluence", "Confluence"), ("sharepoint", "SharePoint"), ("chats", "Project chats")):
        groups.append(f"<div class='rg'><p class='lbl'>{label}</p>{report._link_list(res.get(key))}</div>")
    if res.get("jira") or res.get("other"):
        groups.append("<div class='rg'><p class='lbl'>Other links</p>"
                      + report._link_list((res.get("jira") or []) + (res.get("other") or [])) + "</div>")
    return "<div class='res'>" + "".join(groups) + "</div>"


def _people(p: dict) -> str:
    deck, prop = p.get("deck") or {}, p.get("proposal") or {}
    pm = deck.get("pm") or prop.get("pm") or p.get("project_manager")
    tl = deck.get("tl") or prop.get("tl") or p.get("technical_lead")
    return f"Project Manager: <b>{report._t(pm)}</b> &nbsp;|&nbsp; Technical Lead: <b>{report._t(tl)}</b>"


def _card(p: dict) -> str:
    deck, prop = p.get("deck") or {}, p.get("proposal") or {}
    was = ""
    if _status(deck.get("status"))[0] != _status(prop.get("status"))[0]:
        was = f' <span class="src">was {escape(_status(deck.get("status"))[0])}</span>'
    return (
        f'<details class="card" id="{report._anchor(p.get("name"))}" open>'
        f'<summary class="card-h"><div><h3>{report._t(p.get("name"))}</h3><div class="meta">{_people(p)}</div></div>'
        f"<span>{_pill(prop.get('status'))}{was}</span></summary>"
        f"{report._sec(1, 'Key changes / updates for the period', _key_changes(p))}"
        f"{report._sec(2, 'Roadmap deck: previous information and proposal', _compare(p))}"
        f"{report._sec(3, 'Key project resources', _resources(p))}</details>"
    )


def _toc(projects: list, has_other: bool) -> str:
    def group(text: str) -> str:
        return f"<div class='grp'>{escape(text)}</div>"

    def link(href: str, text: str, dot: str = "") -> str:
        mark = f"<i class='dot {dot}'></i>" if dot else ""
        return f"<a href='#{href}'>{mark}{escape(text)}</a>"

    return (
        "<nav class='toc' aria-label='Contents'>" + link("top", "Go to the top")
        + group("Overview") + link("summary", "Summary") + link("glance", "Projects at a glance")
        + group("Project updates")
        + "".join(link(report._anchor(p.get("name")), str(p.get("name") or NA), _status((p.get("proposal") or {}).get("status"))[1])
                  for p in projects)
        + group("More") + (link("other", "Not on the deck") if has_other else "") + link("sources", "Sources")
        + link("gaps", "Data gaps") + "</nav>"
    )


def _glance(projects: list) -> str:
    rows = []
    for p in projects:
        deck, prop = p.get("deck") or {}, p.get("proposal") or {}
        moved = _status(deck.get("status"))[0] != _status(prop.get("status"))[0]
        change = "Status change" if moved else ("RAG / text updates" if _status_changed(p) or _updated_blocks(p) else "No change")
        rows.append(
            f'<tr><td><a href="#{report._anchor(p.get("name"))}">{report._t(p.get("name"))}</a></td>'
            f"<td>{_pill(deck.get('status'))}</td><td>{_pill(prop.get('status'))}</td><td>{change}</td>"
            f'<td data-s="{_updated_blocks(p):03d}">{_updated_blocks(p)} of {len(BLOCKS)}</td>'
            f"<td>{len(p.get('key_changes') or [])}</td></tr>"
        )
    return ("<table><tr><th>Project</th><th>Previous status (deck)</th><th>Proposed status</th><th>Change</th>"
            "<th>Text blocks updated</th><th>Key changes</th></tr>" + "".join(rows) + "</table>")


def _other(items: list) -> str:
    rows = "".join(
        f"<tr><td>{report._t(i.get('name'))}</td><td>{_pill(i.get('status'))}</td>"
        f"<td>{report._ul([f'<li>{report._rich(s)}</li>' for s in i.get('summary') or []])}</td></tr>"
        for i in items
    )
    return ("<p>Projects in the main reports that are not on the roadmap deck's project slides.</p>"
            "<table><tr><th>Project</th><th>Status in the main report</th><th>Latest updates</th></tr>" + rows + "</table>")


def _sources(data: dict) -> str:
    deck = data.get("deck") or {}
    deck_line = (f"{report._link('I&O Project Roadmap deck', deck.get('url'))}, slides {report._t(deck.get('slides'))}"
                 + (f", last modified {report._t(deck.get('modified'))}" if deck.get("modified") else ""))
    runs = "".join(
        f"<li>{report._link(r.get('run_id'), r.get('url') or brand.sharepoint_file_url(str(r.get('run_id')) + '.html'))}"
        f" <span class='src'>({escape(report._stamp(r.get('generated_at')))})</span></li>"
        for r in data.get("reports") or []
    )
    return (f"<p class='lbl'>Roadmap deck</p><p>{deck_line}</p>"
            f"<p class='lbl'>Main IO Project Assistant reports in the period ({len(data.get('reports') or [])})</p>"
            + (f"<ul>{runs}</ul>" if runs else f"<p>{NA}</p>"))


TITLE_RED = "#ff3b30"  # the red of the "DEV:" tag in the main report's header; the leadership title uses it, the DEV tag turns off-white

LEADERSHIP_CSS = """
:root{--orange:#F79009;--red:#D92D20}
.pill.risk{background:var(--orange);color:var(--off-black)}
.pill.off{background:var(--red);color:var(--off-white)}
.pill.pause{border:1px dashed var(--forest);color:var(--forest);background:var(--off-white)}
nav.toc .dot.risk{background:var(--orange);border-color:var(--orange)}
nav.toc .dot.off{background:var(--red);border-color:var(--red)}
nav.toc .dot.pause{background:var(--off-white);border-style:dashed;border-color:var(--forest)}
.rag{display:inline-block;border-radius:6px;padding:1px 8px;font-size:12px;font-weight:600;white-space:nowrap;border:1px solid var(--off-black)}
.rag.ok{background:var(--spearmint);color:var(--forest)}.rag.risk{background:var(--orange);color:var(--off-black)}
.rag.off{background:var(--red);color:var(--off-white);border-color:var(--red)}.rag.na{color:var(--off-black)}
.res{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:0 32px}
.rg{min-width:0}.rg .lbl{margin-top:.8rem}
.cmp{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1fr);gap:0 24px;margin:.4rem 0}
.cmp .hd{font:700 15px 'Urbanist',Arial,sans-serif;background:var(--forest);color:var(--off-white);padding:8px 12px;border-radius:6px 6px 0 0}
.cmp .hd.new{background:var(--spearmint);color:var(--forest)}
.cmp .rl{grid-column:1/-1;font-weight:700;color:var(--forest);margin:14px 0 2px}
.cmp .cell{min-width:0;padding:6px 12px;border:1px solid rgba(1,82,88,.25);border-radius:6px}
.cmp .cell.chg{background:color-mix(in srgb,var(--spearmint) 14%,transparent);border-color:var(--forest)}
.cmp ul{margin:.1rem 0}
.tag{display:inline-block;margin-left:8px;padding:0 8px;border-radius:999px;font-size:11px;font-weight:600;border:1px solid var(--forest)}
.tag.chg{background:var(--spearmint);color:var(--forest)}.tag.same{opacity:.6}
li.new{list-style:none;margin-left:-1.2rem;padding-left:1.2rem;background:color-mix(in srgb,var(--spearmint) 25%,transparent);border-radius:4px}
li.old{list-style:none;margin-left:-1.2rem;padding-left:1.2rem;opacity:.7;text-decoration:line-through}
li.old .tg{text-decoration:none;display:inline-block}
.tg{font-size:11px;text-transform:uppercase;letter-spacing:.03em;color:var(--forest)}
.src{font-size:12px;font-weight:400;opacity:.85}.why{margin:12px 0 0}
@media (max-width:700px){.cmp,.res{grid-template-columns:minmax(0,1fr)}}
"""


def _validate(data: dict) -> None:
    projects = data.get("projects")
    if not isinstance(projects, list) or not projects:
        raise ValueError("data.json needs a non-empty 'projects' list")
    for p in projects:
        if not p.get("name"):
            raise ValueError("every project needs a 'name'")


def render(data: dict, title: str, compact: bool = False) -> str:
    _validate(data)
    html = _render(data, title, compact)
    return report._shrink(html, report.JIRA_BROWSE) if compact else html


def _render(data: dict, title: str, compact: bool) -> str:
    projects = data["projects"]
    other = data.get("other_projects") or []
    gaps = [g for g in data.get("gaps") or [] if g]
    moved = sum(1 for p in projects if _status((p.get("deck") or {}).get("status"))[0] != _status((p.get("proposal") or {}).get("status"))[0])
    kpis = (
        report._card("Projects on the deck", len(projects))
        + report._card("Status changes proposed", moved, "previous deck status differs")
        + report._card("Projects with updates", sum(1 for p in projects if p.get("key_changes")), "key changes in the period")
        + report._card("Main reports used", len(data.get("reports") or []), "in the analysis period")
        + report._card("Data gaps", len(gaps), "see the Data gaps tab")
    )
    deck_url = report._safe_url((data.get("deck") or {}).get("url"))
    note = brand.header_links() + (
        f' &nbsp;|&nbsp; <a href="{escape(deck_url, quote=True)}" target="_blank" rel="noopener">I&amp;O Project Roadmap deck</a>'
        if deck_url else "")
    gap_body = (f"<p>{len(gaps)} gaps in this run</p>" + report._ul([f"<li>{report._rich(g)}</li>" for g in gaps])
                if gaps else "<p>No data gaps in this run.</p>")
    updates = (
        report._top("Projects at a glance", _glance(projects), fold=True, ident="glance")
        + "<h2>Project updates</h2>" + "".join(_card(p) for p in projects)
        + (report._top("Not on the deck", _other(other), fold=True, ident="other") if other else "")
    )
    return (
        brand.head(title, report.EXTRA_CSS + LEADERSHIP_CSS, fonts=not compact)
        + "<body id='top'>"
        + brand.banner("I&O PROJECTS LEADERSHIP UPDATES", f"Generated: {report._stamp(data.get('generated_at'))}",
                       report._range(data.get("window")), compact=compact, note_html=note, subtitle_last=True,
                       dev=brand.is_dev(title), title_color=TITLE_RED, dev_color=brand.OFF_WHITE)
        + "<div class='wrap layout'>" + _toc(projects, bool(other)) + "<main>"
        + f"<h2 id='summary'>Summary</h2><div class='kpis'>{kpis}</div>"
        + "<p class='tools'>"
        + report._tool("collapse-all", "Collapse all", report.ICON_COLLAPSE)
        + report._tool("expand-all", "Expand all", report.ICON_EXPAND)
        + report._tool("expand-projects", "Expand Proj+SubItems", report.ICON_TREE)
        + "</p>"
        + report._tabs([("tab-projects", "Project updates"), ("tab-sources", "Sources"), ("tab-gaps", "Data gaps")])
        + report._panel("tab-projects", updates)
        + report._panel("tab-sources", report._top("Sources", _sources(data), fold=True, ident="sources"))
        + report._panel("tab-gaps", report._top("Data gaps", gap_body, fold=True, ident="gaps"))
        + brand.footer() + "</main></div>" + brand.foot(report.JIRA_BROWSE)
    )


def build(data_path: Path, compact: bool = False) -> Path:
    """Write <run>/<RUN_ID>.html (compact: <run>/upload/<RUN_ID>.html for the connector upload)."""
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = spend._out_path(data_path.parent, f"{run_id}.html", compact)
    out.write_bytes(render(data, run_id, compact).encode("utf-8"))  # LF endings: bytes match what is uploaded
    return out


# --- Outlook draft and Confluence page -----------------------------------------------------------------------------

def lead_line(window) -> str:
    """'The latest IO Projects Leadership Updates are on SharePoint: period from yyyy/mm/dd till yyyy/mm/dd hh:mm'."""
    period = report.period_text(window)
    return "The latest IO Projects Leadership Updates are on SharePoint:" + (f" {escape(period)}" if period else "")


def render_body(run_id: str, window=None, confluence: bool = False) -> str:
    """Same content for both: lead line, links to the report, the spending report, the SharePoint folder and the
    Confluence parent page, footer (the same layout as the main report's)."""
    br, hr = ("<br />", "<hr />") if confluence else ("<br>", "<hr>")
    link = emaildraft._a
    return (
        f"<p>{lead_line(window)}</p>"
        f"<p>Report: {link(run_id + '.html', brand.sharepoint_file_url(run_id + '.html'))}{br}"
        f"Spending report: {link(run_id + '_spending.html', brand.sharepoint_file_url(run_id + '_spending.html'))}{br}"
        f"Folder: {link('IO Project Assistant Reports', brand.sharepoint_folder_url())}{br}"
        f"Confluence parent page: {link('PMO AI Agent Factory', brand.CONFLUENCE_PARENT_URL)}</p>"
        + hr + emaildraft.footer_block(br)
    )


def build_body(data_path: Path, confluence: bool = False) -> Path:
    """<run>/upload/<RUN_ID>_email.html or <RUN_ID>_confluence.xhtml (same file names as the main report's)."""
    run_id = data_path.parent.name
    window = json.loads(data_path.read_text(encoding="utf-8")).get("window")
    out = spend._out_path(data_path.parent, run_id + ("_confluence.xhtml" if confluence else "_email.html"), True)
    out.write_bytes(render_body(run_id, window, confluence).encode("utf-8"))
    return out
