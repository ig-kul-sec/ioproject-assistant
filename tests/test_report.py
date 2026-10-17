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


def test_spend_cost_none_without_price():
    row = {"agent": "a", "model": "m", "input_tokens": 1000, "output_tokens": 1000, "seconds": 1.0}
    assert spend.cost(row, {}) is None
    assert spend.cost(row, {"m": {"input": 1.0, "output": 2.0}}) == 0.003
