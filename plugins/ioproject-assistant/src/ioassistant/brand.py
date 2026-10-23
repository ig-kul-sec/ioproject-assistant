"""Sectigo brand 2026 (V01.26) styling shared by the HTML reports.

Logos and fonts are bundled in ./brand (copied from the approved sectigo-brand-2026
skill) and inlined as base64 so each report is a single self-contained file.
"""
from __future__ import annotations

import base64
import os
from functools import lru_cache
from html import escape
from pathlib import Path

from . import __version__

BRAND_DIR = Path(__file__).resolve().parent / "brand"

FOREST, SPEARMINT = "#015258", "#06DFC7"
OFF_WHITE, OFF_BLACK = "#F3F2EA", "#333132"
CORAL, SCOUT = "#FF9479", "#7FA9B4"


@lru_cache(maxsize=None)
def _data_uri(name: str, mime: str) -> str:
    path = BRAND_DIR / name
    if not path.is_file():
        return ""
    return f"data:{mime};base64," + base64.b64encode(path.read_bytes()).decode()


def _font_face(family: str, file: str) -> str:
    uri = _data_uri(file, "font/ttf")
    if not uri:
        return ""
    return (
        f"@font-face{{font-family:'{family}';src:url('{uri}') format('truetype');"
        "font-weight:100 900;font-style:normal;font-display:swap}"
    )


CSS_BASE = f"""
:root{{--forest:{FOREST};--spearmint:{SPEARMINT};--off-white:{OFF_WHITE};--off-black:{OFF_BLACK};
--coral:{CORAL};--scout:{SCOUT}}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--off-white);color:var(--off-black);
font:15px/1.5 'DM Sans',Arial,sans-serif}}
h1,h2,h3{{font-family:'Urbanist',Arial,sans-serif;font-weight:700;color:var(--forest);margin:0;line-height:1.15}}
h4{{font-weight:600;font-size:13px;color:var(--forest);margin:1rem 0 .25rem}}
a{{color:var(--forest);text-decoration-color:var(--spearmint);text-underline-offset:2px}}
a:hover{{background:var(--spearmint)}}
header.top{{background:var(--forest);color:var(--off-white);padding:32px 0 36px}}
header.top img{{display:block;width:160px;height:auto;margin-bottom:28px}}
header.top h1{{color:var(--off-white);font-size:38px}}
header.top p{{margin:.5rem 0 0;color:var(--spearmint)}}
header.top p.range{{color:var(--off-white);font-weight:600;font-size:17px}}
.wrap{{max-width:1080px;margin:0 auto;padding:0 24px}}
main.wrap{{padding-top:32px;padding-bottom:48px}}
h2{{font-size:26px;margin:2.5rem 0 1rem}}
table{{border-collapse:collapse;width:100%;font-size:14px}}
th{{text-align:left;font-weight:600;color:var(--forest);border-bottom:2px solid var(--forest);padding:6px 10px}}
td{{padding:6px 10px;border-bottom:1px solid rgba(51,49,50,.18);vertical-align:top}}
footer{{border-top:1px solid rgba(51,49,50,.18);margin-top:3rem;padding-top:1rem;font-size:12px}}
header.top a{{color:var(--spearmint)}}
header.top a:hover{{background:none;color:var(--off-white)}}
header.top p.store{{font-size:13px}}
th.sortable{{cursor:pointer;user-select:none;white-space:nowrap}}
th.sortable:hover{{background:rgba(6,223,199,.25)}}
th.sortable[data-dir=asc]::after{{content:" \\25B2";font-size:10px}}
th.sortable[data-dir=desc]::after{{content:" \\25BC";font-size:10px}}
button.tool{{background:var(--forest);color:var(--off-white);border:0;border-radius:8px;padding:6px 14px;
font:600 13px 'DM Sans',Arial,sans-serif;cursor:pointer;margin-right:8px}}
button.tool{{display:inline-flex;align-items:center;gap:6px}}
button.tool svg{{width:16px;height:16px;fill:none;stroke:currentColor;stroke-width:2;stroke-linecap:round;stroke-linejoin:round}}
button.tool:hover{{background:var(--spearmint);color:var(--forest)}}
"""


def head(title: str, extra_css: str = "", fonts: bool = True) -> str:
    """fonts=False skips the ~450 KB of embedded fonts; CSS then falls back to Arial."""
    font_css = (
        _font_face("Urbanist", "Urbanist-VariableFont_wght.ttf")
        + _font_face("DM Sans", "DMSans-VariableFont_opsz,wght.ttf")
        if fonts else ""
    )
    return (
        "<!doctype html><html lang='en'><head><meta charset='utf-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1'>"
        f"<title>{escape(title)}</title><style>{font_css}{CSS_BASE}{extra_css}</style></head>"
    )


DEV_PREFIX = "DEV_"


def is_dev(run_id: str) -> bool:
    """Runs started from the DEV branch carry the DEV_ prefix in their run id (and so in every file name)."""
    return str(run_id).startswith(DEV_PREFIX)


def banner(title: str, subtitle: str, range_line: str = "", compact: bool = False, note_html: str = "",
           subtitle_last: bool = False, tail_html: str = "", dev: bool = False) -> str:
    """Header band. subtitle_last puts the subtitle (e.g. the Generated line) after the range and link lines.
    dev puts a red "DEV:" in front of the title."""
    # wordmark for the Forest band. Compact builds (connector upload, text only) carry no logo: a model cannot
    # retype the base64 faithfully, and an approximated logo would break the brand rules.
    logo = "" if compact else _data_uri("sectigo-logo-light.png", "image/png")
    img = f"<img src='{logo}' alt='Sectigo'>" if logo else ""
    mark = "<span style='color:#ff3b30'>DEV:</span> " if dev else ""
    return (
        f"<header class='top'><div class='wrap'>{img}<h1>{mark}{escape(title)}</h1>"
        + ("" if subtitle_last else f"<p>{escape(subtitle)}</p>")
        + (f"<p class='range'>{escape(range_line)}</p>" if range_line else "")
        + (f"<p class='store'>{note_html}</p>" if note_html else "")
        + (f"<p>{escape(subtitle)}</p>" if subtitle_last else "")
        + tail_html
        + "</div></header>"
    )


AUTHOR_EMAIL = "igor.kulyk@sectigo.com"
REPO_URL = "https://github.com/ig-kul-sec/ioproject-assistant"
GUIDE_URL = "https://claude.ai/artifact/PvvZeQj7adETgzUuCpRhog?sk=sheeUB2-jY3qJTuYhUBMTQ"
JIRA_BOARD_URL = (
    "https://projects.sectigo.net/secure/RapidBoard.jspa?rapidView=485&projectKey=IOSP"
    "&view=planning.nodetail&issueLimit=100"
)
CONFLUENCE_PARENT_URL = "https://confluence.comodoca.net/display/CO/ITSM+Freshservice"
REPORT_FOLDER_URL = (
    "https://comodoca.sharepoint.com/sites/IOProjectTeam/Shared%20Documents/"
    "ITSM%20Freshservice/Archive/AI%20Test%20SharePoint%20Folder"
)


def footer() -> str:
    return (
        "<footer><p><b>AI AGENT FACTORY:</b> <b>IO Project Assistant</b> &nbsp;|&nbsp; "
        f"Version: {escape(__version__)} &nbsp;|&nbsp; Author: "
        f'<a href="mailto:{AUTHOR_EMAIL}">{AUTHOR_EMAIL}</a> &nbsp;|&nbsp; '
        f'<a href="{GUIDE_URL}" target="_blank" rel="noopener">User-Guide</a> &nbsp;|&nbsp; '
        f'GitHub: <a href="{REPO_URL}" target="_blank" rel="noopener">{REPO_URL}</a></p>'
        "<p>sectigo.com &nbsp;|&nbsp; Sectigo&copy; 2026. All rights reserved.</p></footer>"
    )


def sharepoint_folder_url() -> str:
    """Report folder on SharePoint (SHAREPOINT_REPORT_FOLDER_URL overrides the default)."""
    return (os.environ.get("SHAREPOINT_REPORT_FOLDER_URL") or REPORT_FOLDER_URL).strip()


def sharepoint_file_url(filename: str) -> str:
    """URL of a report file in that folder (the folder URL itself when it has a query string and cannot be extended)."""
    folder = sharepoint_folder_url()
    return folder if "?" in folder else folder.rstrip("/") + "/" + filename


def header_links() -> str:
    """Raw HTML links line for the status report header."""
    return (
        f'<a href="{GUIDE_URL}" target="_blank" rel="noopener">AI AGENT FACTORY</a> &nbsp;|&nbsp; '
        f'<a href="{escape(sharepoint_folder_url(), quote=True)}" target="_blank" rel="noopener">SharePoint Report Archive Link</a>'
        f' &nbsp;|&nbsp; <a href="{CONFLUENCE_PARENT_URL}" target="_blank" rel="noopener">Confluence ITSM Parent Page</a>'
        f' &nbsp;|&nbsp; <a href="{escape(JIRA_BOARD_URL, quote=True)}" target="_blank" rel="noopener">JIRA ScrumBoard</a>'
    )


def sharepoint_note(filename: str) -> str:
    """Raw HTML line linking the report file and its folder on SharePoint."""
    folder = escape(sharepoint_folder_url(), quote=True)
    file_url = sharepoint_file_url(filename)
    file_link = ""
    if file_url != sharepoint_folder_url():
        file_link = f'<a href="{escape(file_url, quote=True)}" target="_blank" rel="noopener">{escape(filename)}</a> in '
    return f'Stored in SharePoint: {file_link}<a href="{folder}" target="_blank" rel="noopener">AI Test SharePoint Folder</a>'


SCRIPT = r"""<script>
(function(){
function val(c){var v=c.getAttribute('data-s');if(v===null)v=c.textContent.trim();return v}
function num(v){var n=parseFloat(String(v).replace(/[$,%]/g,'').replace(/,/g,''));return isNaN(n)||!/^[-$\d.,%\s]+$/.test(v)?null:n}
document.querySelectorAll('table').forEach(function(t){
 t.querySelectorAll('th').forEach(function(h,i){
  h.classList.add('sortable');h.title='Click to sort';
  h.addEventListener('click',function(){
   var asc=h.getAttribute('data-dir')!=='asc';
   t.querySelectorAll('th').forEach(function(x){x.removeAttribute('data-dir')});
   h.setAttribute('data-dir',asc?'asc':'desc');
   var rows=Array.prototype.filter.call(t.rows,function(r){return r.querySelector('td')&&r.parentNode.tagName!=='TFOOT'});
   if(!rows.length)return;var par=rows[0].parentNode;
   rows.sort(function(a,b){
    var x=a.cells[i]?val(a.cells[i]):'',y=b.cells[i]?val(b.cells[i]):'';
    var xe=!x||x==='n/a',ye=!y||y==='n/a';
    if(xe||ye)return xe&&ye?0:(xe?1:-1);
    var nx=num(x),ny=num(y);
    var r=nx!==null&&ny!==null?nx-ny:x.localeCompare(y,undefined,{numeric:true,sensitivity:'base'});
    return asc?r:-r});
   rows.forEach(function(r){par.appendChild(r)});
  })})});
var JB='@@JB@@';
document.querySelectorAll('a.j').forEach(function(a){a.href=JB+a.textContent.trim()});
document.querySelectorAll('a[href^=http]').forEach(function(a){a.target='_blank';a.rel='noopener'});
var tabs=document.querySelectorAll('.tabs button'),panels=document.querySelectorAll('.tabpanel');
function showTab(id){panels.forEach(function(p){p.classList.toggle('on',p.id===id)});
 tabs.forEach(function(b){var on=b.getAttribute('data-tab')===id;b.classList.toggle('on',on);b.setAttribute('aria-selected',on)})}
if(panels.length){document.body.classList.add('tabbed');showTab(panels[0].id);
 tabs.forEach(function(b){b.addEventListener('click',function(){showTab(b.getAttribute('data-tab'))})})}
function openTo(){var id=decodeURIComponent(location.hash.slice(1));var t=id&&document.getElementById(id),e=t,moved=false;
 while(e){if(e.tagName==='DETAILS')e.open=true;
  if(e.classList&&e.classList.contains('tabpanel')&&!e.classList.contains('on')){showTab(e.id);moved=true}
  e=e.parentElement}
 if(moved&&t)t.scrollIntoView()}
window.addEventListener('hashchange',openTo);openTo();
function all(open){document.querySelectorAll('details').forEach(function(d){d.open=open})}
var c=document.getElementById('collapse-all'),x=document.getElementById('expand-all'),pj=document.getElementById('expand-projects');
if(pj)pj.addEventListener('click',function(){document.querySelectorAll('details.card').forEach(function(d){d.open=true});document.querySelectorAll('details.top').forEach(function(d){d.open=!d.classList.contains('fold')});document.querySelectorAll('details.sub').forEach(function(d){d.open=false})});
if(c)c.addEventListener('click',function(){all(false)});
if(x)x.addEventListener('click',function(){all(true)});
})();
</script>"""


def foot(jira_base: str = "") -> str:
    """Closing script and tags. jira_base is the Jira browse URL used to restore links on compact builds."""
    js = SCRIPT.replace("@@JB@@", jira_base.replace("\\", "").replace("'", ""))
    return js + "</body></html>"
