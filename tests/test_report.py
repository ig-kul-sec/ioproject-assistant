import json

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
    assert 'href="https://projects.sectigo.net/browse/IOSP-1012"' in html  # summary ref
    assert 'href="https://projects.sectigo.net/browse/RM-5"' in html  # related ticket
    assert html.index("IOSP-471</a>") < html.index("IOSP-1</a>")  # active before done
    assert "Add backup VLAN IPs" in html and "Move start to 10/18" in html
    assert html.index("What to do</th>") < html.index("Reason/Comment</th>") and "Agreed in the SyncUp" in html
    assert html.index("Description</th>") < html.index("Reason/Comment</th>", html.index("Description</th>")) and "No ticket for the new VLAN" in html
    assert "Version: " in html and "github.com/ig-kul-sec/ioproject-assistant" in html


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


def test_analysis_period_and_generated_format():
    out = report._range({"from": "2026-10-12T00:00:00-04:00", "to": "2026-10-17T19:07:00Z"})
    assert out == "Analysis period: 2026.10.12 - 2026.10.17 15:07 EDT"
    assert report._range(None) == "Analysis period: n/a"
    assert report._stamp("2026-10-17T11:16:29-04:00") == "2026.10.17 11:16 EDT"


def test_text_dates_and_ticket_links():
    out = report._rich("RM-1553 (due 09-11) and COR-11600 (due 2026-08-29) overdue; UTF-8 stays")
    assert "(due 09/11)" in out and "(due 08/29)" in out
    assert 'href="https://projects.sectigo.net/browse/RM-1553"' in out
    assert 'href="https://projects.sectigo.net/browse/COR-11600"' in out
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
    assert html.index("class='kpis'") < html.index("id='collapse-all'") < html.index("Projects at a glance")
    head = html[html.index("<header"):html.index("</header>")]
    assert "Sectigo&copy;" not in head  # both lines are at the end
    assert html.rindex("IO Project Assistant</b>") > html.rindex("Sprint status")
    assert html.rindex("Sectigo&copy; 2026") > html.rindex("Version: ") and html.count("<footer>") == 1
    assert "class='about'" not in html  # same plain footer as the spending report
    assert '<details class="top fold" open><summary class="top"><h2>Projects at a glance</h2>' in html
    assert '<details class="top" open><summary class="top"><h2>Sprint status</h2>' in html
    assert "id='collapse-all'" in html and '<details class="card"' in html and "th.sortable" in html
    assert "I&amp;O PROJECT STATUS REPORT" in html
    assert "SharePoint Report Archive Link</a>" in html and "Confluence ITSM Parent Page</a>" in html
    assert "display/CO/ITSM+Freshservice" in html
    assert "JIRA ScrumBoard</a>" in html and html.count("rapidView=485&amp;projectKey=IOSP") == 2
    assert "Sprint status</h2></summary><p><a " in html and "JIRA ScrumBoard Link</a>" in html
    head = html[html.index("<header"):html.index("</header>")]
    assert head.index("Analysis period") < head.index("SharePoint Report Archive") < head.index("Generated:")
    assert "2026-09-11T" not in html


def test_compact_build_is_smaller_and_restores_links(tmp_path):
    data = {"projects": [{"name": "P", "summary": [{"text": "see IOSP-9 and https://x.test", "tickets": ["IOSP-9"]}]}]}
    full = report.render(data, "R", compact=False)
    small = report.render(data, "R", compact=True)
    assert len(small) < len(full) and '<a class="j">IOSP-9</a>' in small
    assert 'target="_blank"' not in small and "a.j" in small and "browse/IOSP-9" in full
    assert "var JB='https://projects.sectigo.net/browse/'" in small


def test_spending_report_footer_and_sharepoint(tmp_path):
    out = spend.render([{"agent": "a", "model": "m", "input_tokens": 10, "output_tokens": 0, "seconds": 1.0}], {}, "RUN_1")
    assert "Version: " in out and "github.com/ig-kul-sec/ioproject-assistant" in out
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
    assert "Version: " in body and "github.com/ig-kul-sec/ioproject-assistant" in body
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
         "tickets": [{"key": "IOSP-9", "url": "https://projects.sectigo.net/browse/IOSP-9", "status": "In Progress"}, "RM-5"],
         "source": {"label": "Standup 2026-10-14 · closing recap (13:24 UTC)", "url": "https://teams.example/m/2"}},
        {"date": "2026-10-16", "type": "Problem", "title": "Recurring OCSP latency", "status": "RCA open"},
    ]}
    html = report.render(data, "IOProjectAssistantReport_20261016_0900")
    assert "<h2>Daily Ops operational health and incidents</h2>" in html and "Non-project updates" not in html
    assert "2 items from the Daily Ops Standup (Incident: 1, Problem: 1)" in html
    assert "<th>Update by</th>" in html and "Calvin Cochran" in html
    assert html.index("Recurring OCSP latency") < html.index("DNS connector TCP errors")  # newest first
    assert 'href="https://projects.sectigo.net/browse/IOSP-9"' in html and "</a> (In Progress)" in html
    assert 'href="https://projects.sectigo.net/browse/RM-5"' in html and 'href="https://teams.example/m/2"' in html
    assert html.index("incidents</h2>") < html.index("Sprint status</h2>")
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
