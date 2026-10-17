"""Render the status report as a Confluence page body (storage format, plain XHTML, no custom CSS)."""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from . import __version__, brand, report, spend

NA = report.NA


def title_for(run_id: str) -> str:
    """'IOProjectAssistantReport_20261017_1759' -> 'IO Project Assistant Report 20261017 1759 (Draft)'."""
    return run_id.replace("IOProjectAssistantReport", "IO Project Assistant Report").replace("_", " ") + " (Draft)"


def _a(label: str, url: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def _table(head: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return f"<p>{NA}</p>"
    th = "".join(f"<th>{escape(h)}</th>" for h in head)
    tr = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in row) + "</tr>" for row in rows)
    return f"<table><tbody><tr>{th}</tr>{tr}</tbody></table>"


def _list(items: list[str]) -> str:
    return "<ul>" + "".join(f"<li>{i}</li>" for i in items) + "</ul>" if items else f"<p>{NA}</p>"


def _project(p: dict, base: str) -> str:
    out = [f"<h2>{escape(str(p.get('name') or 'Project'))} ({escape(report._rag(p)[0])})</h2>"]
    out.append(
        f"<p>Project Manager: <strong>{report._t(p.get('project_manager'))}</strong> | "
        f"Technical Lead: <strong>{report._t(p.get('technical_lead'))}</strong></p>"
    )
    items = p.get("summary") or [{"text": n} for n in (p.get("notes") or [])[: report.TOP_NOTES]]
    summary = []
    for it in items:
        it = it if isinstance(it, dict) else {"text": it}
        refs = ", ".join(report._ticket_link(k, base) for k in it.get("tickets") or [])
        summary.append(report._rich(it.get("text"), base) + (f" ({refs})" if refs else ""))
    out.append("<h3>Project updates (summary)</h3>" + _list(summary))
    risks = [report._rich(r, base) for r in p.get("risks") or []]
    if risks:
        out.append("<h3>Risks</h3>" + _list(risks))

    ju = p.get("jira_updates") or {}
    names = {str(t.get("key")): t.get("name") or t.get("summary") for t in p.get("tickets") or []}
    change = [
        [report._ticket_link(c, base), report._rich(c.get("name") or c.get("summary") or names.get(str(c.get("key"))), base),
         report._t(c.get("type")), report._rich(c.get("detail"), base)]
        for c in ju.get("change") or []
    ]
    create = [
        [report._rich(c.get("name"), base), report._rich(c.get("description"), base), report._rich(c.get("start")),
         report._rich(c.get("end")), report._t(c.get("owner"))]
        for c in ju.get("create") or []
    ]
    out.append("<h3>Jira task updates needed</h3>")
    if change:
        out.append("<p><strong>Existing tickets to change</strong></p>"
                   + _table(["Ticket", "Ticket name", "Change", "What to do"], change))
    if create:
        out.append("<p><strong>New tickets to create</strong></p>"
                   + _table(["Name", "Description", "Start", "End", "Responsible"], create))
    if not change and not create:
        out.append("<p>No Jira updates identified.</p>")

    tickets = sorted(p.get("tickets") or [], key=lambda t: (report._is_done(t), not t.get("epic")))
    rows = [
        [report._ticket_link(t, base), report._rich(t.get("name") or t.get("summary"), base), report._t(t.get("status")),
         report._t(t.get("assignee")), report._rich(t.get("start")), report._rich(t.get("end") or t.get("due")),
         ", ".join(report._ticket_link(r, base) for r in t.get("related") or []) or NA]
        for t in tickets
    ]
    out.append("<h3>Jira tickets for this project</h3>"
               + _table(["Ticket #", "Ticket name", "Status", "Responsible", "Start", "End", "Related tickets"], rows))
    return "".join(out)


def render(data: dict, run_id: str) -> str:
    base = str(data.get("jira_base_url") or report.JIRA_BROWSE)
    intro = (
        f"<p>Generated: {escape(report._stamp(data.get('generated_at')))} | "
        f"{escape(report._range(data.get('window')))}</p>"
        "<p>Full report with sorting and collapsible sections: "
        + _a(f"{run_id}.html", brand.sharepoint_file_url(f"{run_id}.html")) + " | "
        + _a(f"{run_id}_spending.html", brand.sharepoint_file_url(f"{run_id}_spending.html")) + " | "
        + _a("SharePoint folder with reports", brand.sharepoint_folder_url()) + "</p>"
    )
    gaps = [report._rich(g, base) for g in data.get("gaps") or []]
    footer = (
        f"<hr/><p><strong>IO Project Assistant</strong> | Version: {escape(__version__)} | Author: "
        f'<a href="mailto:{brand.AUTHOR_EMAIL}">{brand.AUTHOR_EMAIL}</a> | GitHub: {_a(brand.REPO_URL, brand.REPO_URL)}</p>'
        "<p>sectigo.com | Sectigo© 2026. All rights reserved.</p>"
    )
    return (
        intro
        + "".join(_project(p, base) for p in data.get("projects", []))
        + ("<h2>Data gaps</h2>" + _list(gaps) if gaps else "")
        + footer
    )


def build(data_path: Path) -> Path:
    data = json.loads(data_path.read_text(encoding="utf-8"))
    run_id = data_path.parent.name
    out = spend._out_path(data_path.parent, f"{run_id}_confluence.xhtml", True)
    out.write_bytes(render(data, run_id).encode("utf-8"))
    return out
