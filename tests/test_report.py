import re
import json
import tempfile
from pathlib import Path

from ioassistant import report, spend

DATA = {
    "generated_at": "2026-10-16T09:00:00",
    "sprint": {
        "name": "Sprint 1", "start": "2026-10-12", "end": "2026-10-16",
        "tickets": [{"key": "IOSP-1", "url": "https://projects.example/IOSP-1", "name": "Patch the sprint server", "status": "Open"}],
    },
    "projects": [{"name": "Proj <A>", "links": {"jira": [{"label": "x", "url": "javascript:alert(1)"}]}}],
}


def test_report_renders_and_escapes(tmp_path):
    run = tmp_path / "IOProjectAssistantReport_20261016_0900"
    run.mkdir()
    (run / "data.json").write_text(json.dumps(DATA), encoding="utf-8")
    html = report.build(run / "data.json").read_text(encoding="utf-8")
    assert 'href="https://projects.example/IOSP-1"' in html
    assert "(5 days)" in html
    assert "Ticket name</th>" in html and "Patch the sprint server" in html
    assert "Proj &lt;A&gt;" in html
    assert 'href="javascript' not in html
    assert "Not rated" in html
    assert "@font-face" in html and "data:image/png;base64" in html
    assert "#FFFFFF" not in html.upper() and "#000000" not in html


def test_report_status_pill(tmp_path):
    data = {"projects": [{"name": "P", "status": "At risk", "risks": ["slip"]}]}
    run = tmp_path / "R_1"
    run.mkdir()
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")
    html = report.build(run / "data.json").read_text(encoding="utf-8")
    assert 'class="pill risk">At risk' in html


def test_spend_cost_none_without_price():
    row = {"agent": "a", "model": "m", "input_tokens": 1000, "output_tokens": 1000, "seconds": 1.0}
    assert spend.cost(row, {}) is None
    assert spend.cost(row, {"m": {"input": 1.0, "output": 2.0}}) == 0.003


def test_per_project_view(tmp_path):
    data = {"projects": [{
        "name": "Rubrik",
        "summary": [{"text": "RAC backup slipped", "tickets": ["IOSP-1012"]}],
        "jira_updates": {
            "change": [{"key": "IOSP-1012", "type": "dates", "detail": "Move start to 10/18",
                        "reason": "Agreed in the SyncUp"}],
            "create": [{"name": "Add backup VLAN IPs", "description": "d", "reason": "No ticket for the new VLAN", "start": "2026-10-17",
                        "end": "2026-10-18", "owner": "Earle"}],
        },
        "links": {"teams": [{"label": "Chat", "url": "https://teams.example/c"}]},
        "tickets": [
            {"key": "IOSP-1", "name": "Done one", "status": "Done", "related": ["RM-5"]},
            {"key": "IOSP-471", "name": "Epic", "status": "In Progress", "epic": True},
        ],
    }]}
    run = tmp_path / "R_2"
    run.mkdir()
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")
    html = report.build(run / "data.json").read_text(encoding="utf-8")
    assert 'href="https://sectigo.atlassian.net/browse/IOSP-1012"' in html  # summary ref
    assert 'href="https://sectigo.atlassian.net/browse/RM-5"' in html  # related ticket
    assert html.index("IOSP-471</a>") < html.index("IOSP-1</a>")  # active before done
    assert "Add backup VLAN IPs" in html and "Move start to 10/18" in html
    assert html.index("What to do</th>") < html.index("Reason/Comment</th>") and "Agreed in the SyncUp" in html
    assert html.index("Description</th>") < html.index("Reason/Comment</th>", html.index("Description</th>")) and "No ticket for the new VLAN" in html
    assert "AI AGENT FACTORY:" in html and "User-Guide</a>" in html and "sk=sheeUB2-jY3qJTuYhUBMTQ" in html and "Version: " in html and "github.com/ig-kul-sec/ioproject-assistant" in html


def test_compact_trims_closed_and_caps_active_tickets(tmp_path):
    tickets = [{"key": f"IOSP-{i}", "name": f"Active {i}", "status": "In Progress"} for i in range(1, 31)]
    tickets += [{"key": f"IOSP-{i}", "name": f"Closed {i}", "status": "Done"} for i in range(101, 106)]
    run = tmp_path / "R_3"
    run.mkdir()
    (run / "data.json").write_text(json.dumps({"projects": [{"name": "Big", "tickets": tickets}]}), encoding="utf-8")
    full = report.build(run / "data.json").read_text(encoding="utf-8")
    small = report.build(run / "data.json", compact=True).read_text(encoding="utf-8")
    assert "Closed 101" in full and "Active 30" in full and "left out of this copy" not in full
    assert "Closed 101" not in small and "Active 30" not in small
    assert f"Active {report.COMPACT_TICKET_CAP}<" in small and "15 tickets are left out of this copy" in small


def _render_data(tmp_path, data):
    run = Path(tempfile.mkdtemp(dir=tmp_path)) / "R_4"
    run.mkdir()
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")
    return report.build(run / "data.json").read_text(encoding="utf-8")


def test_shorthand_ticket_lists_are_linked(tmp_path):
    data = {"projects": [{"name": "P", "summary": [{"text": "Status email: IOSP-1004/1005 moved; also RM-1658, 1661 and COR-5, 12 hosts"}]}]}
    html = _render_data(tmp_path, data)
    assert 'IOSP-1004</a>/<a href="https://sectigo.atlassian.net/browse/IOSP-1005"' in html
    assert 'RM-1658</a>, <a href="https://sectigo.atlassian.net/browse/RM-1661"' in html
    assert "COR-5</a>, 12 hosts" in html  # different digit count: left as plain text


def test_project_tickets_show_sprint(tmp_path):
    data = {"sprint": {"name": "I&O 26.43", "tickets": [{"key": "IOSP-7", "name": "a", "status": "Open"}]},
            "projects": [{"name": "P", "tickets": [
                {"key": "IOSP-7", "name": "In sprint", "status": "Open"},
                {"key": "IOSP-8", "name": "Elsewhere", "status": "Open", "sprint": "I&O 26.42"},
                {"key": "IOSP-9", "name": "None", "status": "Open"}]}]}
    html = _render_data(tmp_path, data)
    assert "Sprint</th>" in html and "I&amp;O 26.43</td>" in html and "I&amp;O 26.42</td>" in html


def test_sprint_status_subsections(tmp_path):
    cur = {"name": "I&O 26.43", "start": "2026-10-19", "end": "2026-10-23", "tickets": [{"key": "IOSP-1", "status": "Open"}]}
    past = {"name": "I&O 26.42", "start": "2026-10-12", "end": "2026-10-16", "tickets": [{"key": "IOSP-2", "status": "Open"}]}
    both = _render_data(tmp_path, {"sprint": cur, "past_sprint": past})
    assert both.index("Past sprint I&amp;O 26.42 (not closed yet)</summary>") < both.index("Current sprint I&amp;O 26.43</summary>")
    assert both.count('<details class="sub" open><summary class="sec"><span>1</span> Past sprint') == 1
    assert "I&amp;O 26.42</b>" in both and "I&amp;O 26.43</b>" in both
    older = {"name": "I&O 26.41", "start": "2026-10-05", "end": "2026-10-09", "tickets": [{"key": "IOSP-3", "status": "Open"}]}
    many = _render_data(tmp_path, {"sprint": cur, "past_sprints": [older, past]})
    assert many.index("Past sprint I&amp;O 26.41") < many.index("Past sprint I&amp;O 26.42") < many.index("Current sprint I&amp;O 26.43</summary>")
    assert "<span>3</span> Current sprint" in many
    only = _render_data(tmp_path, {"sprint": cur})
    assert "Past sprint" not in only and "<span>1</span> Current sprint" in only


def test_spend_total_row_sums_tokens_seconds_cost():
    rows = [{"agent": "a", "model": "claude-sonnet-5-5", "input_tokens": 1000, "output_tokens": 0, "seconds": 10.5},
            {"agent": "b", "model": "claude-opus-5-5", "input_tokens": 2000, "output_tokens": 0, "seconds": 4.5}]
    html = spend.render(rows, spend.load_pricing(), "R")
    assert "<tfoot><tr class='total'><td><b>Total</b></td><td></td><td><b>3,000</b></td><td><b>15.0</b></td><td><b>0.01$</b></td>" in html


def test_analysis_period_and_generated_format():
    out = report._range({"from": "2026-10-12T00:00:00-04:00", "to": "2026-10-17T19:07:00Z"})
    assert out == "Analysis period: 2026.10.12 - 2026.10.17 15:07 EDT"
    assert report._range(None) == "Analysis period: n/a"
    assert report._stamp("2026-10-17T11:16:29-04:00") == "2026.10.17 11:16 EDT"


def test_text_dates_and_ticket_links():
    out = report._rich("RM-1553 (due 09-11) and COR-11600 (due 2026-08-29) overdue; UTF-8 stays")
    assert "(due 09/11)" in out and "(due 08/29)" in out
    assert 'href="https://sectigo.atlassian.net/browse/RM-1553"' in out
    assert 'href="https://sectigo.atlassian.net/browse/COR-11600"' in out
    assert "UTF-8" in out and "browse/UTF" not in out


def test_report_features(tmp_path):
    data = {
        "generated_at": "2026-10-17T11:16:29-04:00",
        "projects": [{
            "name": "Rubrik", "project_manager": "Pat", "technical_lead": "Lee",
            "tickets": [{"key": "IOSP-9", "name": "RAC backup start", "status": "Open", "end": "2026-09-11"}],
            "jira_updates": {"change": [{"key": "IOSP-9", "type": "dates", "detail": "move to 2026-10-18"}]},
        }],
    }
    run = tmp_path / "R_3"
    run.mkdir()
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")
    html = report.build(run / "data.json").read_text(encoding="utf-8")
    assert "<th>Ticket name</th>" in html and html.count("RAC backup start") >= 2  # name looked up from tickets
    assert 'data-s="2026-09-11">09/11</td>' in html
    assert "Project Manager: <b>Pat</b>" in html and "Technical Lead: <b>Lee</b>" in html
    assert "Generated: 2026.10.17 11:16 EDT" in html
    assert "id='expand-projects'" in html and html.count("<svg viewBox='0 0 24 24'") == 3 and "Expand Proj+SubItems" in html
    assert html.index("class='kpis'") < html.index("id='collapse-all'") < html.index("<h2>Projects at a glance")
    head = html[html.index("<header"):html.index("</header>")]
    assert "Sectigo&copy;" not in head  # both lines are at the end
    assert html.rindex("IO Project Assistant</b>") > html.rindex("JIRA tickets")
    assert html.rindex("Sectigo&copy; 2026") > html.rindex("Version: ") and html.count("<footer>") == 1
    assert "class='about'" not in html  # same plain footer as the spending report
    assert '<details class="top fold" id="glance" open><summary class="top"><h2>Projects at a glance</h2>' in html
    assert '<details class="top" id="sprint" open><summary class="top"><h2>JIRA tickets</h2>' in html
    assert "id='collapse-all'" in html and '<details class="card"' in html and "th.sortable" in html
    assert "I&amp;O PROJECT STATUS REPORT" in html
    assert "SharePoint Report Archive Link</a>" in html and "Confluence ITSM Parent Page</a>" in html
    assert "wiki/spaces/CO/pages/94177160/ITSM+Freshservice" in html
    assert "AI AGENT FACTORY</a>" in html and html.index("AI AGENT FACTORY</a>") < html.index("SharePoint Report Archive Link") and "JIRA ScrumBoard</a>" in html and html.count("boards/318/backlog") == 2
    assert "JIRA ScrumBoard Link</a>" in html and html.index("JIRA ScrumBoard Link</a>") < html.index("<h2>Sprint charts</h2>") < html.index("<h2>JIRA tickets</h2>")
    head = html[html.index("<header"):html.index("</header>")]
    assert head.index("Analysis period") < head.index("SharePoint Report Archive") < head.index("Generated:")
    assert "2026-09-11T" not in html


def test_compact_build_is_ascii_safe_for_upload():
    data = {"projects": [{"name": "P", "summary": [{"text": "a · b – c"}]}]}
    small = report.render(data, "R", compact=True)
    assert "·" not in small and "–" not in small and "&middot;" in small


def test_contents_rail_links_sections_and_projects():
    data = {"gaps": ["Jira: token expired"], "projects": [{"name": "Rubrik"}, {"name": "Oracle RAC"}]}
    html = report.render(data, "R")
    nav = html[html.index("<nav class='toc'"):html.index("</nav>")]
    assert html.index("<nav class='toc'") < html.index("<main>") and "class='wrap layout'" in html
    for target in ("summary", "glance", "ops", "sprint-charts", "sprint", "gaps"):
        assert f"href='#{target}'" in nav and (f"id='{target}'" in html or f'id="{target}"' in html)
    assert nav.count("class='dot ") == 2 and "Rubrik</a>" in nav and "Oracle RAC</a>" in nav
    assert "href='#gaps'" not in report.render({"projects": []}, "R")
    assert nav.index("href='#top'") < nav.index("href='#summary'") and "Go to the top</a>" in nav
    assert "id='top'" in html


def test_dev_run_gets_red_dev_prefix_in_both_banners():
    dev = report.render({"projects": []}, "DEV_IOProjectAssistantReport_20261023_1400")
    assert "<h1><span style='color:#ff3b30'>DEV:</span> I&amp;O PROJECT STATUS REPORT</h1>" in dev
    prod = report.render({"projects": []}, "IOProjectAssistantReport_20261023_1400")
    assert "DEV:" not in prod
    row = [{"agent": "a", "model": "m", "input_tokens": 1, "output_tokens": 1, "seconds": 1.0}]
    assert "DEV:</span>" in spend.render(row, {}, "DEV_IOProjectAssistantReport_20261023_1400")
    assert "DEV:" not in spend.render(row, {}, "IOProjectAssistantReport_20261023_1400")


def test_tabs_split_projects_operations_sprint_and_gaps():
    data = {"gaps": ["Jira: token expired"], "projects": [{"name": "Rubrik"}]}
    html = report.render(data, "R")
    bar = html[html.index("<div class='tabs'"):html.index("</div>", html.index("<div class='tabs'"))]
    labels = [t for t in ("Projects", "Operations", "Sprint management", "Data gaps") if f">{t}</button>" in bar]
    assert labels == ["Projects", "Operations", "Sprint management", "Data gaps"]
    assert html.index("class='tools'") < html.index("class='tabs'") < html.index("id='tab-projects'")

    def panel(ident):
        start = html.index(f"id='{ident}'")
        ends = [i for i in (html.find("<section class='tabpanel'", start + 1), html.index("</main>")) if i > 0]
        return html[start:min(ends)]
    assert 'id="glance"' in panel("tab-projects") and "Rubrik" in panel("tab-projects")
    assert 'id="ops"' in panel("tab-ops") and 'id="ops"' not in panel("tab-projects")
    assert 'id="sprint"' in panel("tab-sprint") and 'id="sprint"' not in panel("tab-projects")
    assert 'id="gaps"' in panel("tab-gaps") and 'id="gaps"' not in panel("tab-sprint")
    no_gaps = report.render({"projects": []}, "R")
    assert "tab-gaps" not in no_gaps and "Sprint management" in no_gaps


def test_compact_build_is_smaller_and_restores_links(tmp_path):
    data = {"projects": [{"name": "P", "summary": [{"text": "see IOSP-9 and https://x.test", "tickets": ["IOSP-9"]}]}]}
    full = report.render(data, "R", compact=False)
    small = report.render(data, "R", compact=True)
    assert len(small) < len(full) and '<a class="j">IOSP-9</a>' in small
    assert 'target="_blank"' not in small and "a.j" in small and "browse/IOSP-9" in full
    assert "var JB='https://sectigo.atlassian.net/browse/'" in small


def test_spending_report_footer_and_sharepoint(tmp_path):
    out = spend.render([{"agent": "a", "model": "m", "input_tokens": 10, "output_tokens": 0, "seconds": 1.0}], {}, "RUN_1")
    assert "AI AGENT FACTORY:" in out and "User-Guide</a>" in out and "sk=sheeUB2-jY3qJTuYhUBMTQ" in out and "Version: " in out and "github.com/ig-kul-sec/ioproject-assistant" in out
    assert "Sectigo&copy; 2026. All rights reserved." in out
    assert "Stored in SharePoint:" in out and "RUN_1_spending.html" in out and "<script>" in out


def test_spend_splits_total_tokens_by_output_share():
    row = {"agent": "a", "model": "m", "input_tokens": 1000, "output_tokens": 0, "seconds": 1.0}
    pricing = {"_output_share": 0.1, "m": {"input": 1.0, "output": 10.0}}
    assert spend.cost(row, pricing) == (900 * 1.0 + 100 * 10.0) / 1_000_000


def test_confluence_body_and_email_draft(tmp_path):
    from xml.dom import minidom

    from ioassistant import confluence, emaildraft

    run = tmp_path / "IOProjectAssistantReport_20261017_1759"
    run.mkdir()
    data = {"generated_at": "2026-10-17T11:16:29-04:00", "projects": [{
        "name": "Rubrik <DR>", "project_manager": "Pat", "summary": [{"text": "RM-1553 due 2026-09-11", "tickets": ["IOSP-1"]}],
        "tickets": [{"key": "IOSP-1", "name": "T & U", "status": "Open"}],
    }]}
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")
    body = confluence.build(run / "data.json").read_text(encoding="utf-8")
    minidom.parseString(f"<r>{body}</r>")  # well-formed XML
    assert "Rubrik" not in body  # same content as the email, not the per-project report
    assert "The latest I&amp;O project status report is on SharePoint:" in body
    assert "AI AGENT FACTORY:" in body and "User-Guide</a>" in body and "sk=sheeUB2-jY3qJTuYhUBMTQ" in body and "Version: " in body and "github.com/ig-kul-sec/ioproject-assistant" in body
    assert "Sectigo© 2026. All rights reserved." in body
    assert confluence.title_for(run.name) == "TEST: IO Project Assistant Report 20261017 1759 (Draft)"
    mail = emaildraft.build(run / "data.json").read_text(encoding="utf-8")
    assert "AI%20Test%20SharePoint%20Folder/IOProjectAssistantReport_20261017_1759.html" in mail
    assert "Sectigo\u00a9 2026. All rights reserved." in mail and "<span" not in mail and "<img" not in mail
    assert emaildraft.subject_for(run.name) == "IO Project Assistant Report 20261017 1759"


def test_daily_ops_section():
    data = {"projects": [], "non_project": [
        {"date": "2026-10-14", "type": "Incident", "title": "DNS connector TCP errors", "detail": "Matches the maintenance window",
         "status": "Owner to confirm", "reported_by": "Calvin Cochran", "owner": None,
         "tickets": [{"key": "IOSP-9", "url": "https://sectigo.atlassian.net/browse/IOSP-9", "status": "In Progress"}, "RM-5"],
         "source": {"label": "Standup 2026-10-14 · closing recap (13:24 UTC)", "url": "https://teams.example/m/2"}},
        {"date": "2026-10-16", "type": "Problem", "title": "Recurring OCSP latency", "status": "RCA open"},
    ]}
    html = report.render(data, "IOProjectAssistantReport_20261016_0900")
    assert "<h2>Daily Ops operational health and incidents</h2>" in html and "Non-project updates" not in html
    assert "2 items from the Daily Ops Standup (Incident: 1, Problem: 1)" in html
    assert "<th>Update by</th>" in html and "Calvin Cochran" in html
    assert html.index("Recurring OCSP latency") < html.index("DNS connector TCP errors")  # newest first
    assert 'href="https://sectigo.atlassian.net/browse/IOSP-9"' in html and "</a> (In Progress)" in html
    assert 'href="https://sectigo.atlassian.net/browse/RM-5"' in html and 'href="https://teams.example/m/2"' in html
    assert html.index("incidents</h2>") < html.index("Sprint charts</h2>")
    assert "No Daily Ops operational updates in this period." in report.render({"projects": []}, "IOProjectAssistantReport_20261016_0900")


def test_repeated_source_links_are_merged_or_numbered():
    recap = "Standup recap 2026-10-14"
    links = {"sources": [
        {"label": recap, "url": "https://teams.example/m/1"},
        {"label": recap, "url": "https://teams.example/m/2"},
        {"label": recap, "url": "https://teams.example/m/1"},  # same message twice
    ]}
    html = report.render({"projects": [{"name": "P", "links": links}]}, "IOProjectAssistantReport_20261014_0900")
    assert "sources (2)" in html
    assert html.count("https://teams.example/m/1") == 1
    assert "Standup recap 10/14 (1)" in html and "Standup recap 10/14 (2)" in html


def test_sprint_charts_show_status_and_load_per_employee():
    tickets = [
        {"key": "IOSP-1", "status": "Done", "assignee": "Ann"},
        {"key": "IOSP-2", "status": "In Progress", "assignee": "Ann"},
        {"key": "IOSP-3", "status": "Backlog", "assignee": "Bob"},
        {"key": "IOSP-4", "status": "Backlog"},
    ]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "projects": []}, "R")
    assert "<h2>Sprint charts</h2>" in html and "Tickets by status" in html and "Tickets by employee" in html
    assert "2 employees account for 3 of 4 tickets" in html and "1 unassigned" in html
    assert "Tickets by status" not in report.render({"sprint": {"name": "S1", "tickets": []}, "projects": []}, "R")


TEAMS = {"as_of": "2026-10-23", "teams": [
    {"name": "DBA", "manager": "Prajeet Singh Kahlon", "manager_email": "prajeet.singh@sectigo.com",
     "members": [{"name": "Vlad Serbanescu", "email": "vlad.serbanescu@sectigo.com"}]},
    {"name": "Network", "manager": "Jaime Larsen", "members": [{"name": "Shane Feola"}]},
]}


def test_sprint_charts_group_tickets_by_team_from_ardoq_roster():
    tickets = [
        {"key": "IOSP-1", "status": "Done", "assignee": "Vlad Serbanescu"},
        {"key": "IOSP-2", "status": "Open", "assignee": "Prajeet Singh Kahlon"},
        {"key": "IOSP-3", "status": "Open", "assignee": "shane  feola"},
        {"key": "IOSP-4", "status": "Open", "assignee": "Karl Witt"},
        {"key": "IOSP-5", "status": "Open"},
    ]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "org_teams": TEAMS, "projects": []}, "R")
    assert "Tickets by team" in html and "DBA (Prajeet Singh Kahlon)" in html and "Network (Jaime Larsen)" in html
    assert "Other: Karl Witt (1)" in html and "live for this run" in html
    assert "<td>DBA</td><td>Prajeet Singh Kahlon</td><td>2</td><td>2</td><td>1</td><td>1</td><td>1.0</td>" in html
    assert "static snapshot" not in html  # a live roster raises no data gap


def test_static_roster_snapshot_is_flagged_as_data_gap():
    data = {"sprint": {"name": "S1", "tickets": [{"key": "IOSP-1", "status": "Open", "assignee": "Calvin Cochran"}]},
            "projects": []}
    html = report.render(data, "R")
    assert "SRE Tier 2 (Calvin Cochran)" in html and "static snapshot dated" in html
    assert "Ardoq was not connected for this run" in html and "id='tab-gaps'" in html


def test_sprint_statuses_follow_workflow_order():
    names = ["Done", "QA", "Unassigned", "Rejected", "On Hold", "In Progress", "To Do", "Backlog"]
    tickets = [{"key": f"IOSP-{i}", "status": s} for i, s in enumerate(names, 1)]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "projects": []}, "R")
    chart = html[html.index("Tickets by status"):html.index("Tickets by team")]
    order = [m.group(1) for m in re.finditer(r"<span class='bl'>([^<]+)</span>", chart)]
    assert order == ["Backlog", "To Do", "In Progress", "QA", "On Hold", "Unassigned", "Done", "Rejected", "Total"]
    table = html[html.index("All 8 sprint tickets"):]
    keys = [int(k) for k in re.findall(r"<td>IOSP-(\d+)</td>", table)][:8]
    assert keys == [8, 7, 6, 2, 5, 3, 1, 4]


def test_idle_employees_per_team_listed_without_tickets():
    tickets = [
        {"key": "IOSP-1", "status": "Done", "assignee": "Vlad Serbanescu"},
        {"key": "IOSP-2", "status": "Open", "assignee": "shane feola"},
    ]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "org_teams": TEAMS, "projects": []}, "R")
    section = html[html.index("Employees without tickets assigned in sprint"):]
    section = section[:section.index("</table>")]
    assert "<td>DBA</td><td>Prajeet Singh Kahlon</td><td>0 of 1</td><td>everyone has a ticket</td>" in section
    assert "<td>Network</td><td>Jaime Larsen</td><td>0 of 1</td><td>everyone has a ticket</td>" in section
    assert "Vlad Serbanescu" not in section and "Shane Feola" not in section


def test_totals_cover_all_tickets_and_employees_show_their_team():
    tickets = [
        {"key": "IOSP-1", "status": "Done", "assignee": "Vlad Serbanescu"},
        {"key": "IOSP-2", "status": "Open", "assignee": "Karl Witt"},
        {"key": "IOSP-3", "status": "Open"},
        {"key": "IOSP-4", "status": "Backlog"},
    ]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "org_teams": TEAMS, "projects": []}, "R")
    status = html[html.index("Tickets by status"):html.index("Tickets by team")]
    team = html[html.index("Tickets by team"):html.index("Tickets by employee")]
    assert "<span class='bl'>Total</span><span class='bt'></span><span class='bv'>4</span>" in status
    assert "<span class='bl'>Total</span><span class='bt'></span><span class='bv'>4</span>" in team
    assert "<td>Unassigned</td><td>no assignee</td><td>n/a</td><td>2</td>" in team
    assert "<td><b>Total</b></td><td></td><td>4</td><td><b>4</b></td><td><b>1</b></td><td><b>3</b></td>" in team
    assert "Vlad Serbanescu (DBA)" in html and "Karl Witt (Other)" in html


def test_employee_chart_has_unassigned_row_and_total():
    tickets = [
        {"key": "IOSP-1", "status": "Done", "assignee": "Vlad Serbanescu"},
        {"key": "IOSP-2", "status": "Open", "assignee": "Karl Witt"},
        {"key": "IOSP-3", "status": "Open"},
        {"key": "IOSP-4", "status": "Done"},
    ]
    html = report.render({"sprint": {"name": "S1", "tickets": tickets}, "org_teams": TEAMS, "projects": []}, "R")
    emp = html[html.index("Tickets by employee"):html.index("<h2>JIRA tickets</h2>")]
    assert "<span class='bl'>Unassigned</span>" in emp and "<span class='bv'>2</span></div>" in emp
    assert "<span class='bl'>Total</span><span class='bt'></span><span class='bv'>4</span>" in emp
    no_gap = report.render({"sprint": {"name": "S1", "tickets": tickets[:2]}, "org_teams": TEAMS, "projects": []}, "R")
    assert "<span class='bl'>Unassigned</span>" not in no_gap[no_gap.index("Tickets by employee"):no_gap.index("<h2>JIRA tickets</h2>")]


def _issue(key, *histories):
    return {"key": key, "fields": {"summary": f"{key} task", "status": {"name": "Open"}, "assignee": {"displayName": "Ann"}},
            "changelog": {"histories": [
                {"created": c, "author": {"displayName": by},
                 "items": [{"field": "Sprint", "from": f, "fromString": fs, "to": t, "toString": ts}]}
                for c, by, f, fs, t, ts in histories]}}


def test_sprint_changes_from_day_two_with_date_and_author():
    from ioassistant import sprintchanges
    issues = [
        _issue("IOSP-1", ("2026-10-19T10:00:00.000+0100", "Day One", None, None, "1017", "S2")),       # day 1: ignored
        _issue("IOSP-2", ("2026-10-20T12:00:00.000+0100", "Gabriel Rovira", "1016", "S1", "1016, 1017", "S1, S2")),
        _issue("IOSP-3", ("2026-10-21T09:30:00.000+0100", "Maarten Broekman", "1016, 1017", "S1, S2", "1016", "S1"),
               ("2026-10-22T09:30:00.000+0100", "Calvin Cochran", "1016", "S1", "1018", "S3")),            # unrelated: ignored
        _issue("IOSP-4", ("2026-10-21T10:00:00.000+0100", "Ann", "1017", "S2", "1018", "S3")),
    ]
    rows = sprintchanges.extract(issues, 1017, "2026-10-19")
    assert [(r["key"], r["action"], r["date"], r["by"], r["other_sprint"]) for r in rows] == [
        ("IOSP-2", "added", "2026-10-20", "Gabriel Rovira", "S1"),
        ("IOSP-3", "removed", "2026-10-21", "Maarten Broekman", "S1"),
        ("IOSP-4", "removed", "2026-10-21", "Ann", "S3"),
    ]


def test_sprint_changes_section_and_sprint_link():
    sprint = {"name": "I&O 26.43", "start": "2026-10-19", "tickets": [{"key": "IOSP-9", "status": "Open"}],
              "changes": [{"key": "IOSP-2", "url": "https://j/IOSP-2", "name": "Patch", "status": "Open", "assignee": "Ann",
                           "action": "added", "date": "2026-10-20", "by": "Gabriel Rovira", "other_sprint": "I&O 26.42"}]}
    html = report.render({"sprint": sprint, "projects": []}, "R")
    sec = html[html.index("Tickets added or removed from the sprint"):]
    sec = sec[:sec.index("</table>")]
    assert "from day 2 of the sprint (10/20) onward: 1 added, 0 removed" in sec.lower().replace("from day 2", "from day 2")
    assert "<td>10/20</td>" in sec or 'data-s="2026-10-20">10/20</td>' in sec
    assert "Gabriel Rovira" in sec and "<td>Added</td>" in sec
    assert ">JIRA Tickets Link: Sprint I&amp;O 26.43</a>" in html
    assert "issues/?jql=sprint%20%3D%20%22I%26O%2026.43%22%20order%20by%20updated%20DESC" in html
    assert "Tickets added or removed" not in report.render({"sprint": {**sprint, "changes": None}, "projects": []}, "R")


def test_ticket_created_straight_into_sprint_counts_as_added_by_creator():
    from ioassistant import sprintchanges
    new = {"key": "COR-9", "fields": {"summary": "New", "status": {"name": "Open"}, "created": "2026-10-22T19:23:11.365+0100",
                                      "creator": {"displayName": "Maarten Broekman"}}, "changelog": {"histories": []}}
    old = {**new, "key": "COR-8", "fields": {**new["fields"], "created": "2026-10-19T09:00:00.000+0100"}}
    rows = sprintchanges.extract([new, old], 1017, "2026-10-19", members={"COR-9", "COR-8"})
    assert [(r["key"], r["action"], r["date"], r["by"]) for r in rows] == [("COR-9", "added", "2026-10-22", "Maarten Broekman")]


def test_sprint_changes_failure_leaves_data_file_untouched(tmp_path, monkeypatch):
    import pytest
    from ioassistant import sprintchanges

    def boom(*args):
        raise SystemExit("Jira answered HTTP 401 (for 401/403 check JIRA_API_TOKEN)")

    monkeypatch.setattr(sprintchanges, "fetch", boom)
    path = tmp_path / "data.json"
    path.write_bytes(b'{\r\n "sprint": {"name": "S1", "start": "2026-10-19"}\r\n}')
    before = path.read_bytes()
    with pytest.raises(SystemExit):
        sprintchanges.build(path)
    assert path.read_bytes() == before


def test_sprint_changes_keeps_the_data_file_layout(tmp_path, monkeypatch):
    from ioassistant import sprintchanges
    monkeypatch.setattr(sprintchanges, "fetch", lambda *a: [{"key": "COR-1", "action": "added", "date": "2026-10-20"}])
    path = tmp_path / "data.json"
    path.write_bytes(b'{\r\n "sprint": {\r\n  "name": "S\xc3\xa9",\r\n  "start": "2026-10-19"\r\n }\r\n}')
    sprintchanges.build(path)
    raw = path.read_bytes()
    assert b"\r\n" in raw and b"\n" not in raw.replace(b"\r\n", b"") and "S\u00e9".encode() in raw
    assert json.loads(raw)["sprint"]["changes"][0]["key"] == "COR-1"
