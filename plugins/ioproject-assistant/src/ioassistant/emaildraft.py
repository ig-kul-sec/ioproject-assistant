"""Subject and body for the Outlook draft that points to the report on SharePoint.

The body uses only tags the Outlook connector allows (p, a, strong, hr): no style, span or img.
"""
from __future__ import annotations

from html import escape
from pathlib import Path

from . import __version__, brand, spend

CC = "igor.kulyk@sectigo.com"


def subject_for(run_id: str) -> str:
    """'IOProjectAssistantReport_20261017_1759' -> 'IO Project Assistant Report 20261017 1759'."""
    return run_id.replace("IOProjectAssistantReport", "IO Project Assistant Report").replace("_", " ")


def _a(label: str, url: str) -> str:
    return f'<a href="{escape(url, quote=True)}">{escape(label)}</a>'


def render(run_id: str) -> str:
    return (
        "<p>The latest I&amp;O project status report is on SharePoint:</p>"
        f"<p>Report: {_a(run_id + '.html', brand.sharepoint_file_url(run_id + '.html'))}<br>"
        f"Spending report: {_a(run_id + '_spending.html', brand.sharepoint_file_url(run_id + '_spending.html'))}<br>"
        f"Folder: {_a('IO Project Assistant Reports', brand.sharepoint_folder_url())}</p>"
        "<hr>"
        f"<p><strong>AI AGENT FACTORY:</strong> <strong>IO Project Assistant</strong> | Version: {escape(__version__)} | Author: "
        f'<a href="mailto:{brand.AUTHOR_EMAIL}">{brand.AUTHOR_EMAIL}</a> | {_a('User-Guide', brand.GUIDE_URL)} | GitHub: {_a(brand.REPO_URL, brand.REPO_URL)}<br>'
        "sectigo.com | Sectigo© 2026. All rights reserved.</p>"
    )


def build(data_path: Path) -> Path:
    """Write <run>/upload/<RUN_ID>_email.html; the run id is the run folder name."""
    run_id = data_path.parent.name
    out = spend._out_path(data_path.parent, f"{run_id}_email.html", True)
    out.write_bytes(render(run_id).encode("utf-8"))
    return out
