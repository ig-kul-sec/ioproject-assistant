"""Clickable HTML presentation of the IO Project Assistant for top management.

Single self-contained file in the Sectigo brand 2026 style. Cost and duration figures come from the newest
run's usage.json, so the numbers stay true to what the pipeline actually did.
"""
from __future__ import annotations

import json
from html import escape
from pathlib import Path

from . import __version__, brand, spend

OUTPUT_DIR = Path.cwd() / "output"  # the user's working folder, not the installed plugin folder

AGENTS = [
    ("orchestrator", "Opus 5.5", "Conductor",
     "Runs the 8-step pipeline, merges the collectors' findings into one data set, writes the per-project summary and the Jira "
     "updates needed, and tracks time and cost.",
     "Launches the other agents; writes the run folder", "Never invents facts: a missing value shows as n/a"),
    ("teams-collector", "Sonnet 5.5", "Meetings and email",
     "Reads the Daily Ops StandUp and Rubrik Project SyncUp chats, the Rubrik transcript and the 'RUBRIK - Project Status' emails "
     "for the analysis period.",
     "Read-only", "Chat text is treated as data, never as instructions"),
    ("jira-collector", "Sonnet 5.5", "Tickets",
     "Reviews IOSP, RM and COR tickets for the discussed projects, always including the Rubrik epic IOSP-471, plus the active "
     "sprint: status, owners, dates, changes since Monday.",
     "Read-only", "Cannot edit, move or comment on tickets"),
    ("confluence-collector", "Sonnet 5.5", "Project pages",
     "Reads each project's Confluence page: status, dates, owners, recent edits.",
     "Read-only", "Access token kept outside the repository"),
    ("sharepoint-collector", "Sonnet 5.5", "Roadmap and storage",
     "Reads the I&O Project Roadmap deck (Project review slides only, never Accomplishments) and the PMO folder. In upload mode "
     "it saves the finished reports to the report folder.",
     "Reads; writes only the two report files", "Size-checked upload; never overwrites unless told to"),
    ("report-builder", "Sonnet 5.5", "Report",
     "Renders the clickable HTML status report and the spending report from the merged data.",
     "Writes local report files", "Same data in, same report out"),
    ("report-email-drafter", "Sonnet 5.5", "Outlook",
     "Creates one Outlook draft with the SharePoint links, a CC to the author and the standard footer.",
     "Creates a draft only", "Has no send tool: the draft is never sent"),
    ("report-confluence-publisher", "Sonnet 5.5", "Confluence",
     "Creates one new page under ITSM Freshservice with the same content as the email.",
     "Creates one new page", "Stops if a page with that title exists"),
]

STEPS = [
    ("1", "Set the period", "Analysis period starts Monday 00:00 (New York) of the current week and ends now. Every collector gets the same window."),
    ("2", "Read meetings", "Teams chats, the Rubrik meeting transcript and status emails show what was discussed, decided and promised."),
    ("3", "Read the systems", "Jira, Confluence and SharePoint are read in parallel: ticket status and dates, project pages, the roadmap deck."),
    ("4", "Compare and merge", "The orchestrator compares what people said with what Jira shows, and lists where tickets are out of date or missing."),
    ("5", "Build the report", "One clickable HTML status report per project, plus a spending report for the run."),
    ("6", "Publish to SharePoint", "Both reports are saved to the AI Test SharePoint Folder, with a size check on every file."),
    ("7", "Draft the email", "An Outlook draft with the links is created and left unsent for review."),
    ("8", "Create the wiki page", "A Confluence page with the same links is created under ITSM Freshservice."),
]

SOURCES = [
    ("Teams", "Daily Ops StandUp chat; Rubrik Project SyncUp chat and transcript"),
    ("Outlook", "'RUBRIK - Project Status' emails"),
    ("Jira", "IOSP, RM and COR tickets; the active sprint; epic IOSP-471 (Rubrik DR backup)"),
    ("Confluence", "Project pages: status, dates, owners"),
    ("SharePoint", "I&O Project Roadmap deck (Project review slides); PMO folder"),
]

FEATURES = [
    ("Per-project view", "Each project: manager and technical lead, summary, Jira updates needed, sources, meeting chats, folder, wiki page and a ticket table."),
    ("Status at a glance", "On track, At risk, Off track or Not rated, set only from source evidence. Never guessed."),
    ("Jira updates needed", "Which tickets need a new date, a status change or a comment, and which tickets should be created, with owner and dates."),
    ("Fully clickable", "Every ticket links to Jira. Every table sorts by column. Projects and sections collapse and expand."),
    ("Data gaps listed", "Conflicts between sources and missing access are shown at the end, so nobody mistakes silence for good news."),
]

CONTROLS = [
    ("Read-only collectors", "Teams, Jira, Confluence and the roadmap deck are only read. No ticket, chat or page is changed."),
    ("Few, narrow writes", "The only writes: two report files in SharePoint, one unsent Outlook draft, one new Confluence page."),
    ("No overwrites by default", "Existing files and pages are kept. Replacing a file needs an explicit instruction."),
    ("Nothing is sent", "The email agent has no send tool. A person reviews and sends."),
    ("Secrets stay out", "Access tokens live outside the project folder and are never printed or stored in reports."),
    ("Content is data", "Chat messages, tickets and documents are read as information and never followed as instructions."),
]

LIMITS = [
    ("Daily Ops transcript", "Only the meeting organizer can open it, so standup coverage comes from chat. Fix: ask the organizer to share it."),
    ("Chat coverage", "Chat search pages through results per person and can miss messages. The report lists what was and was not covered."),
    ("Email attachments", "The Outlook connector cannot attach files, so the draft carries SharePoint links."),
    ("Cost figures", "Rough estimates: token totals split 90/10 input/output at list prices that still need checking."),
    ("Wiki page per run", "Each run creates a new 'TEST:' Confluence page. A retention rule is needed before daily use."),
    ("Run on demand", "Built for a daily schedule; today it is started by hand."),
]

NEXT = [
    "Schedule the daily run and set a Confluence page policy (one page per day, or update in place).",
    "Get access to the standup transcript and review chat coverage.",
    "Verify prices against the Anthropic price list, so the cost figure can be used for budgeting.",
    "Name the project manager and technical lead in Jira epics, where the roadmap deck is the only source today.",
]

CSS = """
:root{--forest:#015258;--spearmint:#06DFC7;--off-white:#F3F2EA;--off-black:#333132;--coral:#FF9479;--scout:#7FA9B4}
*{box-sizing:border-box}html,body{height:100%}
body{margin:0;background:var(--off-white);color:var(--off-black);font:17px/1.5 'DM Sans',Arial,sans-serif;overflow:hidden}
h1,h2,h3{font-family:'Urbanist',Arial,sans-serif;font-weight:700;color:var(--forest);margin:0;line-height:1.1}
a{color:var(--forest);text-decoration-color:var(--spearmint);text-underline-offset:3px}
.bar{position:fixed;top:0;left:0;right:0;height:64px;background:var(--forest);display:flex;align-items:center;justify-content:space-between;padding:0 28px;z-index:5}
.bar img{width:160px;height:auto;display:block}.bar span{color:var(--spearmint);font-weight:600;font-size:14px}
.slide{position:absolute;inset:64px 0 56px 0;padding:36px 56px;display:none;overflow:auto}
.slide.on{display:block}
.slide h2{font-size:42px;margin-bottom:6px}.lead{font-size:20px;max-width:900px;margin:8px 0 26px}
.title{background:var(--forest);color:var(--off-white);display:none;flex-direction:column;justify-content:center}
.title.on{display:flex}.title h1{color:var(--off-white);font-size:64px;max-width:900px}
.title p{color:var(--spearmint);font-size:24px;margin:14px 0 0;max-width:800px}.title .meta{color:var(--off-white);font-size:15px;margin-top:36px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:16px}
.card{background:var(--forest);color:var(--off-white);border-radius:12px;padding:20px 22px}
.card h3{color:var(--spearmint);font-size:22px;margin-bottom:8px}.card p{margin:0}
.card.light{background:transparent;color:var(--off-black);border:1px solid var(--forest)}.card.light h3{color:var(--forest)}
.flow{display:flex;flex-wrap:wrap;gap:10px;align-items:stretch;margin:6px 0 18px}
button.node,button.agent{font:inherit;text-align:left;cursor:pointer;border-radius:12px;border:2px solid var(--forest);background:transparent;color:var(--forest);padding:12px 14px}
button.node{flex:1 1 140px;min-width:140px}button.node b{display:block;font:700 18px 'Urbanist',Arial,sans-serif;color:var(--spearmint);background:var(--forest);width:34px;height:34px;border-radius:50%;text-align:center;line-height:34px;margin-bottom:8px}
button.node.on,button.agent.on,button.node:hover,button.agent:hover{background:var(--forest);color:var(--off-white)}
.detail{border-left:6px solid var(--spearmint);padding:14px 18px;min-height:76px;font-size:18px;border-radius:0 8px 8px 0;background:rgba(1,82,88,.08)}
.agents{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:12px}
button.agent small{display:block;opacity:.8;font-size:13px;margin-top:2px}button.agent b{font:700 17px 'Urbanist',Arial,sans-serif}
.rows{display:grid;gap:10px}.row{display:grid;grid-template-columns:200px 1fr;gap:16px;padding:12px 0;border-bottom:1px solid rgba(51,49,50,.18)}
.row b{font-family:'Urbanist',Arial,sans-serif;color:var(--forest);font-size:19px}
.kpis{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:16px;margin-bottom:22px}
.kpi{background:var(--forest);border-radius:12px;padding:18px 20px;color:var(--off-white)}.kpi i{display:block;font:700 40px/1 'Urbanist',Arial,sans-serif;color:var(--spearmint);font-style:normal}
.bars{display:grid;gap:8px}.bar2{display:grid;grid-template-columns:230px 1fr 70px;gap:12px;align-items:center;font-size:15px}
.bar2 div.track{background:rgba(1,82,88,.12);border-radius:6px;height:16px}.bar2 div.fill{background:var(--forest);height:16px;border-radius:6px}
.bar2 span:last-child{text-align:right;font-weight:600}.note{font-size:14px;opacity:.85;margin-top:14px}
ul.next{margin:0;padding-left:1.2rem}ul.next li{margin:8px 0;font-size:19px}
.nav{position:fixed;left:0;right:0;bottom:0;height:56px;background:var(--off-white);border-top:1px solid rgba(51,49,50,.18);display:flex;align-items:center;justify-content:space-between;padding:0 28px;z-index:5}
.nav button{font:600 15px 'DM Sans',Arial,sans-serif;background:var(--forest);color:var(--off-white);border:0;border-radius:8px;padding:8px 18px;cursor:pointer}
.nav button:hover{background:var(--spearmint);color:var(--forest)}.nav button:disabled{opacity:.35;cursor:default}
.dots{display:flex;gap:8px}.dots button{width:12px;height:12px;padding:0;border-radius:50%;background:rgba(1,82,88,.3)}
.dots button.on{background:var(--forest)}.count{font-size:14px}
.links a{display:inline-block;margin:6px 18px 6px 0;font-weight:600}
@media print{body{overflow:visible}.slide{position:static;display:block!important;page-break-after:always}.bar,.nav{display:none}}
@media (max-width:700px){.slide{padding:24px 18px}.slide h2{font-size:32px}.title h1{font-size:40px}.row{grid-template-columns:1fr}.bar2{grid-template-columns:1fr 60px}.bar2 span:first-child{grid-column:1/3}}
"""

JS = """
(function(){
var slides=[].slice.call(document.querySelectorAll('.slide')),dots=document.getElementById('dots'),n=0;
function show(i){n=Math.max(0,Math.min(slides.length-1,i));slides.forEach(function(s,k){s.classList.toggle('on',k===n)});
 [].forEach.call(dots.children,function(d,k){d.classList.toggle('on',k===n)});
 document.getElementById('prev').disabled=n===0;document.getElementById('next').disabled=n===slides.length-1;
 document.getElementById('count').textContent=(n+1)+' / '+slides.length;history.replaceState(null,'','#'+(n+1))}
slides.forEach(function(s,k){var d=document.createElement('button');d.setAttribute('aria-label','Slide '+(k+1));d.onclick=function(){show(k)};dots.appendChild(d)});
document.getElementById('prev').onclick=function(){show(n-1)};document.getElementById('next').onclick=function(){show(n+1)};
document.addEventListener('keydown',function(e){if(e.key==='ArrowRight'||e.key==='PageDown')show(n+1);if(e.key==='ArrowLeft'||e.key==='PageUp')show(n-1)});
document.querySelectorAll('[data-pick]').forEach(function(group){var out=document.getElementById(group.getAttribute('data-pick'));
 var btns=[].slice.call(group.querySelectorAll('button'));
 btns.forEach(function(b){b.onclick=function(){btns.forEach(function(x){x.classList.remove('on')});b.classList.add('on');out.innerHTML=b.getAttribute('data-detail')}});
 if(btns.length)btns[0].click()});
var h=parseInt(location.hash.slice(1),10);show(isNaN(h)?0:h-1);
})();
"""


def _latest_usage() -> tuple[str, list[dict]] | None:
    runs = sorted(OUTPUT_DIR.glob("IOProjectAssistantReport_*/usage.json"))
    if not runs:
        return None
    return runs[-1].parent.name, json.loads(runs[-1].read_text(encoding="utf-8"))


def _cards(items, light=False) -> str:
    cls = "card light" if light else "card"
    return "".join(f"<div class='{cls}'><h3>{escape(t)}</h3><p>{escape(d)}</p></div>" for t, d in items)


def _rows(items) -> str:
    return "".join(f"<div class='row'><b>{escape(t)}</b><span>{escape(d)}</span></div>" for t, d in items)


def _cost_slide() -> str:
    latest = _latest_usage()
    if not latest:
        return "<p class='lead'>No run data yet. Run the orchestrator to see time and cost.</p>"
    run_id, rows = latest
    pricing = spend.load_pricing()
    costs = [(r["agent"], spend.cost(r, pricing) or 0.0, r["input_tokens"] + r["output_tokens"], r["seconds"]) for r in rows]
    total = sum(c for _, c, _, _ in costs)
    minutes = max((r["seconds"] for r in rows), default=0) / 60
    peak = max((c for _, c, _, _ in costs), default=0) or 1
    bars = "".join(
        f"<div class='bar2'><span>{escape(a)}</span><div class='track'><div class='fill' style='width:{100 * c / peak:.0f}%'></div></div>"
        f"<span>{c:.2f}$</span></div>"
        for a, c, _, _ in sorted(costs, key=lambda x: -x[1])
    )
    return (
        "<div class='kpis'>"
        f"<div class='kpi'><i>{total:.2f}$</i>estimated cost of one run</div>"
        f"<div class='kpi'><i>{minutes:.0f} min</i>start to finish</div>"
        f"<div class='kpi'><i>{len(rows)}</i>agent runs in the pipeline</div>"
        f"<div class='kpi'><i>{sum(t for _, _, t, _ in costs) / 1000:,.0f}k</i>tokens processed</div></div>"
        f"<div class='bars'>{bars}</div>"
        f"<p class='note'>Latest run: {escape(run_id)}. Rough estimates: token totals split 90% input / 10% output at list prices, "
        "caching discounts ignored. Prices still need checking before budgeting.</p>"
    )


def render() -> str:
    agents = "".join(
        "<button class='agent' data-detail=\""
        + escape(f"<b>{n}</b> ({m}, {role}). {d} Access: {acc}. Guardrail: {g}.", quote=True)
        + f"\"><b>{escape(n)}</b><small>{escape(m)} | {escape(role)}</small></button>"
        for n, m, role, d, acc, g in AGENTS
    )
    steps = "".join(
        f"<button class='node' data-detail=\"{escape(d, quote=True)}\"><b>{k}</b>{escape(t)}</button>" for k, t, d in STEPS
    )
    slides = [
        "<section class='slide title'><h1>IO Project Assistant</h1>"
        "<p>One clickable status report per project, built from the systems we already use.</p>"
        f"<div class='meta'>Version {escape(__version__)} | Author {brand.AUTHOR_EMAIL}</div></section>",

        "<section class='slide'><h2>What it does</h2>"
        "<p class='lead'>Every project update lives in a different place. The assistant reads them all, compares them, and says "
        "where reality and the ticket system disagree.</p><div class='grid'>"
        + _cards([
            ("Collects", "Teams meetings, status emails, Jira tickets, Confluence pages and the roadmap deck, for the same period."),
            ("Compares", "Checks what was said in meetings against what Jira shows, and flags tickets that are out of date."),
            ("Reports", "A per-project status report with owners, risks and the Jira changes needed, published where the team already looks."),
        ]) + "</div></section>",

        "<section class='slide'><h2>How a run works</h2><p class='lead'>Eight steps. Click a step for the detail.</p>"
        f"<div class='flow' data-pick='stepd'>{steps}</div><div class='detail' id='stepd'></div></section>",

        "<section class='slide'><h2>The agents</h2><p class='lead'>One conductor and seven specialists. Each does one job with the "
        "least access it needs. Click an agent.</p>"
        f"<div class='agents' data-pick='agentd'>{agents}</div><div class='detail' id='agentd' style='margin-top:16px'></div></section>",

        "<section class='slide'><h2>What it reads</h2><p class='lead'>Existing systems only. Nothing new for the teams to fill in.</p>"
        f"<div class='rows'>{_rows(SOURCES)}</div></section>",

        "<section class='slide'><h2>What management gets</h2><p class='lead'>A report built to be scanned in minutes and clicked "
        f"through for detail.</p><div class='grid'>{_cards(FEATURES, light=True)}</div></section>",

        "<section class='slide'><h2>Built-in controls</h2><p class='lead'>It reports and drafts. People decide and send.</p>"
        f"<div class='rows'>{_rows(CONTROLS)}</div></section>",

        f"<section class='slide'><h2>Time and cost</h2><p class='lead'>Measured on the latest run.</p>{_cost_slide()}</section>",

        "<section class='slide'><h2>Known limits</h2><p class='lead'>Stated up front, and each one is also listed in the report's data gaps.</p>"
        f"<div class='rows'>{_rows(LIMITS)}</div></section>",

        "<section class='slide'><h2>Next steps</h2><p class='lead'>What turns this from a working pilot into a daily routine.</p>"
        "<ul class='next'>" + "".join(f"<li>{escape(x)}</li>" for x in NEXT) + "</ul>"
        "<p class='links' style='margin-top:30px'>"
        f"<a href='{escape(brand.sharepoint_folder_url(), quote=True)}' target='_blank' rel='noopener'>SharePoint report archive</a>"
        f"<a href='{brand.CONFLUENCE_PARENT_URL}' target='_blank' rel='noopener'>Confluence ITSM parent page</a>"
        f"<a href='{brand.REPO_URL}' target='_blank' rel='noopener'>GitHub repository</a></p></section>",
    ]
    logo = brand._data_uri("sectigo-logo-light.png", "image/png")
    return (
        brand.head("IO Project Assistant", CSS)
        + "<body><div class='bar'>" + (f"<img src='{logo}' alt='Sectigo'>" if logo else "")
        + "<span>IO Project Assistant</span></div>"
        + "".join(slides)
        + "<div class='nav'><button id='prev'>Previous</button><div class='dots' id='dots'></div>"
        "<span class='count' id='count'></span><button id='next'>Next</button></div>"
        f"<script>{JS}</script></body></html>"
    )


def build(out: Path | None = None) -> Path:
    out = out or OUTPUT_DIR / "IOProjectAssistant_Presentation.html"
    out.parent.mkdir(exist_ok=True)
    out.write_bytes(render().encode("utf-8"))
    return out
