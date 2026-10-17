import json

from ioassistant import report, spend

DATA = {
    "generated_at": "2026-10-16T09:00:00",
    "sprint": {
        "name": "Sprint 1", "start": "2026-10-12", "end": "2026-10-16",
        "tickets": [{"key": "IOSP-1", "url": "https://projects.example/IOSP-1", "status": "Open"}],
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
            "change": [{"key": "IOSP-1012", "type": "dates", "detail": "Move start to 10/18"}],
            "create": [{"name": "Add backup VLAN IPs", "description": "d", "start": "2026-10-17",
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
    assert "Version: " in html and "github.com/ig-kul-sec/ioproject-assistant" in html
