"""IO Projects Leadership Updates: digest of the main reports, the report, and the email / Confluence bodies."""
import io
import json
import re
from contextlib import redirect_stdout
from datetime import datetime
from pathlib import Path

import pytest

from ioassistant import cli, confluence, emaildraft, leadership

TZ = leadership.TZ
PERIOD = (datetime(2026, 10, 30, 0, 0, tzinfo=TZ), datetime(2026, 11, 6, 12, 0, tzinfo=TZ))


def _main_run(output, run_id, projects, gaps=None):
    run = output / run_id
    run.mkdir(parents=True)
    (run / f"{run_id}.html").write_text("<html></html>", encoding="utf-8")
    data = {"generated_at": "2026-11-05T10:08:00-05:00", "window": {"from": "2026-11-02T00:00:00-05:00", "to": "2026-11-05T10:08:00-05:00"},
            "projects": projects, "gaps": gaps or []}
    (run / "data.json").write_text(json.dumps(data), encoding="utf-8")


def _project(name, status="On track", summary=("did a thing",), **extra):
    return {"name": name, "status": status, "summary": [{"text": s, "tickets": ["IOSP-1"]} for s in summary], **extra}


def _cli(run, command):
    buf = io.StringIO()
    with redirect_stdout(buf):
        cli.main([command, str(run / "data.json")])
    return Path(buf.getvalue().strip())


@pytest.fixture
def output(tmp_path):
    out = tmp_path / "output"
    _main_run(out, "IOProjectAssistantReport_20261103_1000", [
        _project("Rubrik DR backup", "At risk", ("shipment planned", "kickoff done"), risks=["arrival date unknown"],
                 tickets=[{"key": "IOSP-471", "name": "Rubrik", "epic": True, "status": "In Progress"}],
                 links={"teams": [{"label": "chat", "url": "https://teams.example/c1"}]}),
        _project("Internal audit"),
    ])
    _main_run(out, "IOProjectAssistantReport_20261105_1008", [
        _project("Rubrik DR backup", "Off track", ("shipment planned", "appliances arrived"),
                 links={"teams": [{"label": "chat", "url": "https://teams.example/c1"}, {"label": "new chat", "url": "https://teams.example/c2"}]}),
        _project("Quarterly audit evidence"),
        _project("Postgres EDB migration"),
    ], gaps=["Jira: token expired"])
    _main_run(out, "IOProjectAssistantReport_20261020_1000", [_project("Rubrik DR backup")])  # before the period
    _main_run(out, "DEV_IOProjectAssistantReport_20261104_1000", [_project("Rubrik DR backup")])  # DEV is never read for PROD
    (out / "IOProjectAssistantReport_20261104_1500").mkdir()  # a run folder without data.json is skipped
    return out


def test_names():
    assert leadership.is_leadership("IOProjectLeadershipUpdates_20261105_1008")
    assert leadership.is_leadership("DEV_IOProjectLeadershipUpdates_20261105_1008")
    assert not leadership.is_leadership("IOProjectAssistantReport_20261105_1008")
    assert emaildraft.subject_for("IOProjectLeadershipUpdates_20261105_1008") == "IO Projects Leadership Updates 20261105 1008"
    assert confluence.title_for("IOProjectLeadershipUpdates_20261105_1008") == "TEST: IO Projects Leadership Updates 20261105 1008 (Draft)"
    assert emaildraft.subject_for("IOProjectAssistantReport_20261017_1759") == "IO Project Assistant Report 20261017 1759"


def test_alias_matching():
    aliases = leadership.load_aliases()
    pairs = {
        "HSM (update TSA signers)": "HSM Upgrade", "Network 2.0 (Manchester)": "Network v2.0", "Postgres EDB migration": "Postgres DB",
        "EoL servers and OS upgrades": "Migration EOL/EOS OSs", "Rubrik DR backup": "Rubrik", "Oracle RAC": "Oracle RAC",
        "Internal audit evidence": None, "SCM internal deployment (Gateway agent, COR-11767)": None,
    }
    for report_name, deck_name in pairs.items():
        assert leadership.match_project(report_name, aliases) == deck_name, report_name


def test_collect_digest(output):
    d = leadership.collect(output, *PERIOD)
    assert [r["run_id"][-13:] for r in d["runs"]] == ["20261103_1000", "20261105_1008"]  # no DEV, no old, no empty folder
    rubrik = next(p for p in d["projects"] if p["deck_name"] == "Rubrik")
    assert rubrik["found"] and rubrik["latest"]["status"] == "Off track"  # the newest run wins
    assert [h["status"] for h in rubrik["status_history"]] == ["At risk", "Off track"]
    texts = [u["text"] for u in rubrik["updates"]]
    assert texts == ["appliances arrived", "kickoff done", "shipment planned"]  # newest first, repeated text kept once
    assert next(u for u in rubrik["updates"] if u["text"] == "shipment planned")["run_id"].endswith("20261103_1000")
    assert rubrik["risks"] == ["arrival date unknown"]
    assert [e["key"] for e in rubrik["resources"]["epics"]] == ["IOSP-471"]
    assert [c["url"] for c in rubrik["resources"]["chats"]] == ["https://teams.example/c2", "https://teams.example/c1"]
    assert not next(p for p in d["projects"] if p["deck_name"] == "Debian OS lifecycle management")["found"]
    assert [u["name"] for u in d["unmatched_report_projects"]] == ["Quarterly audit evidence"]  # newest run only
    assert d["newest_report_gaps"] == ["Jira: token expired"]
    assert "2026-11-02" in d["days_without_report"] and "2026-11-03" not in d["days_without_report"]
    assert "2026-11-06" not in d["days_without_report"]  # the last day is still running


def test_collect_reads_dev_runs_only_for_dev(output):
    d = leadership.collect(output, *PERIOD, dev=True)
    assert any(r["run_id"].startswith("DEV_") for r in d["runs"])


STATE_DECK = {"status": "Off Track", "schedule": "R", "scope": "G", "cost": "G", "pm": "Igor", "tl": "Calvin",
              "accomplishments": ["Old item", "Kept item"], "whats_next": ["Ship <appliances>"], "issues": [],
              "risks": ["Arrival date unknown"], "dependencies": [], "milestones": ["Next milestone: Nov 9"]}
STATE_NEW = dict(STATE_DECK, status="At risk", schedule="Y", accomplishments=["Kept item", "Appliances arrived IOSP-471"])
DATA = {
    "generated_at": "2026-11-06T11:00:00-05:00", "window": {"from": "2026-10-30T00:00:00-04:00", "to": "2026-11-06T11:00:00-05:00"},
    "deck": {"url": "https://example.sharepoint.com/deck.pptx", "slides": "5-9", "modified": "2026-11-06"},
    "reports": [{"run_id": "IOProjectAssistantReport_20261105_1008", "generated_at": "2026-11-05T10:08:00-05:00"}],
    "projects": [
        {"name": "Rubrik <DR>", "slide": 6, "deck": STATE_DECK, "proposal": STATE_NEW, "rationale": "Appliances arrived (IOSP-471).",
         "key_changes": [{"text": "Appliances arrived", "date": "2026-11-05", "source": "IOProjectAssistantReport_20261105_1008"}],
         "resources": {"epics": [{"key": "IOSP-471", "name": "Rubrik", "status": "In Progress"}],
                       "chats": [{"label": "chat", "url": "https://teams.example/c1"}, {"label": "bad", "url": "javascript:alert(1)"}]}},
        {"name": "Oracle RAC", "slide": 5, "deck": STATE_DECK, "proposal": STATE_DECK},
    ],
    "other_projects": [{"name": "Internal audit evidence", "status": "On track", "summary": ["evidence collected"]}],
    "gaps": ["Debian: no report data"],
}


def _run_dir(tmp_path, name="IOProjectLeadershipUpdates_20261106_1100"):
    run = tmp_path / name
    run.mkdir()
    (run / "data.json").write_text(json.dumps(DATA), encoding="utf-8")
    return run


def test_report_layout(tmp_path):
    run = _run_dir(tmp_path)
    html = leadership.build(run / "data.json").read_text(encoding="utf-8")
    # header: white title, the word LEADERSHIP underlined and highlighted
    h1 = html[html.index("<h1"):html.index("</h1>")]
    assert h1.startswith("<h1 style='color:#FFFFFF'>") and "I&amp;O PROJECTS " in h1 and " UPDATES" in h1
    assert re.search(r"<span style='text-decoration:underline[^']*background:rgba\(6,223,199[^']*'>LEADERSHIP</span>", h1)
    tabs = re.findall(r"<button role='tab' data-tab='[^']+'>([^<]+)</button>", html)
    assert tabs == ["Project updates", "Sources", "Data gaps"]  # Sources is the 2nd tab
    panel_sources = html.index("id='tab-sources'")
    assert html.index("id='tab-projects'") < panel_sources < html.index("id='tab-gaps'")
    assert panel_sources < html.index("Main IO Project Assistant reports in the period") < html.index("id='tab-gaps'")
    # inside a card: key changes, then the deck comparison, then the resources
    card = html[html.index('<details class="card"'):]
    assert (card.index("Key changes / updates for the period") < card.index("Roadmap deck: previous information and proposal")
            < card.index("Key project resources"))
    # resources: two-column grid in the order Jira epics, Confluence, SharePoint, Project chats
    res = card[card.index("class='res'"):]
    assert res.index("Jira epic") < res.index(">Confluence<") < res.index(">SharePoint<") < res.index(">Project chats<")
    assert ".res{display:grid;grid-template-columns:repeat(2" in html
    # colours: At risk orange, Off track red
    assert ".pill.risk{background:var(--orange)" in html and "--orange:#F79009" in html
    assert ".pill.off{background:var(--red)" in html and "--red:#D92D20" in html
    assert "Previous information: roadmap deck (slide 6)" in html and "Proposal: new statuses" in html
    assert 'class="pill off">Off track' in html and 'class="pill risk">At risk' in html and "was Off track" in html
    assert "Rubrik &lt;DR&gt;" in html and "Ship &lt;appliances&gt;" in html and "Rubrik <DR>" not in html
    assert 'class="new"' in html and "Superseded" in html  # changed text is marked on both sides
    assert 'href="javascript' not in html
    assert "Debian: no report data" in html and "Not on the deck" in html and "Internal audit evidence" in html
    assert "1 of 6" in html  # Rubrik changed only its accomplishments
    assert "report 11/05 10:08" in html  # the key change links to the main report
    assert "no change proposed" in html  # Oracle RAC is unchanged
    assert "@font-face" in html and "data:image/png;base64" in html


def test_report_compact_and_dev(tmp_path):
    run = _run_dir(tmp_path, "DEV_IOProjectLeadershipUpdates_20261106_1100")
    out = leadership.build(run / "data.json", compact=True)
    html = out.read_text(encoding="utf-8")
    assert out.parent.name == "upload" and "@font-face" not in html and "data:image" not in html
    assert "<span style='color:#F3F2EA'>DEV:</span>" in html and "<h1 style='color:#FFFFFF'>" in html  # white tag and white title


def test_paused_projects_go_last():
    paused = {"status": "Paused"}
    data = {"projects": [
        {"name": "Alpha Paused", "deck": {"status": "On track"}, "proposal": paused},  # paused by the proposal
        {"name": "Beta Paused", "deck": paused},                                       # paused by the deck, no proposal status
        {"name": "Gamma Active", "deck": {"status": "On track"}, "proposal": {"status": "At risk"}},
        {"name": "Delta Resumed", "deck": paused, "proposal": {"status": "On track"}},  # resumed: stays in the main list
    ]}
    html = leadership.render(data, "IOProjectLeadershipUpdates_1_1")
    cards = html[html.index('<details class="card"'):]
    order = [cards.index(n) for n in ("Gamma Active", "Delta Resumed", "Alpha Paused", "Beta Paused")]
    assert order == sorted(order)  # active ones first in their original order, then the paused ones in theirs


def test_main_report_header_is_unchanged(tmp_path):
    from ioassistant import report

    run = tmp_path / "DEV_IOProjectAssistantReport_20261106_1054"
    run.mkdir()
    (run / "data.json").write_text(json.dumps({"projects": [{"name": "P"}]}), encoding="utf-8")
    html = report.build(run / "data.json").read_text(encoding="utf-8")
    assert "<h1><span style='color:#ff3b30'>DEV:</span> " in html  # the main report keeps its red DEV tag and plain title


def test_report_needs_projects():
    with pytest.raises(ValueError):
        leadership.render({"projects": []}, "IOProjectLeadershipUpdates_1_1")
    with pytest.raises(ValueError):
        leadership.render({"projects": [{"deck": {}}]}, "IOProjectLeadershipUpdates_1_1")


def test_email_and_confluence_bodies(tmp_path):
    run = _run_dir(tmp_path)
    email = _cli(run, "email").read_text(encoding="utf-8")
    page = _cli(run, "confluence").read_text(encoding="utf-8")
    for body, br in ((email, "<br>"), (page, "<br />")):
        assert "The latest IO Projects Leadership Updates are on SharePoint: period from 2026/10/30 till 2026/11/06 11:00" in body
        assert "IOProjectLeadershipUpdates_20261106_1100.html" in body and "Confluence parent page" in body
        assert "AI AGENT FACTORY" in body and "Sectigo© 2026" in body and br in body
        assert "Spending report: " in body and "IOProjectLeadershipUpdates_20261106_1100_spending.html" in body
        assert body.index("Report: ") < body.index("Spending report: ") < body.index("Folder: <a")  # same layout as the main report
    assert email.endswith("</p>")  # no trailing newline: the upload byte count must match
    assert (run / "upload" / "IOProjectLeadershipUpdates_20261106_1100_email.html").is_file()
    assert (run / "upload" / "IOProjectLeadershipUpdates_20261106_1100_confluence.xhtml").is_file()


USAGE = [
    {"agent": "collector-sharepoint", "model": "claude-sonnet-5-5", "input_tokens": 59506, "output_tokens": 0, "seconds": 146.0},
    {"agent": "orchestrator", "model": "claude-opus-5-5", "input_tokens": 0, "output_tokens": 0, "seconds": 1242.6,
     "note": "tokens are filled in by the launching session"},
]


def test_spending_report_for_a_leadership_run(tmp_path):
    from ioassistant import spend

    run = _run_dir(tmp_path, "DEV_IOProjectLeadershipUpdates_20261106_1100")
    usage = run / "usage.json"
    usage.write_text(json.dumps(USAGE), encoding="utf-8")
    spend.set_orchestrator(usage, 162818, 1242.6)  # the same fill-in step as the main report
    full = spend.build(usage)
    compact = spend.build(usage, compact=True)
    assert full.name == "DEV_IOProjectLeadershipUpdates_20261106_1100_spending.html"
    assert compact.parent.name == "upload" and compact.name == full.name  # the upload copy has the same file name the email links to
    html = full.read_text(encoding="utf-8")
    assert "collector-sharepoint" in html and "orchestrator" in html and "162,818" in html and "DEV:" in html
    assert "I&amp;O PROJECTS LEADERSHIP UPDATES run - SPENDING" in html and "run spending" not in html  # the leadership header
    assert "I&amp;O PROJECTS LEADERSHIP UPDATES run - SPENDING" in compact.read_text(encoding="utf-8")
    main = spend.render(USAGE, spend.load_pricing(), "IOProjectAssistantReport_20261106_1054")
    assert "I&amp;O assistant run spending" in main and "LEADERSHIP" not in main  # the main report keeps its header
    assert "n/a" not in html.split("<tfoot>")[1].split("</tfoot>")[0]  # both models are priced, so the total is a number
    assert "data:image" not in compact.read_text(encoding="utf-8")


def test_main_report_email_is_unchanged(tmp_path):
    run = tmp_path / "IOProjectAssistantReport_20261106_1054"
    run.mkdir()
    (run / "data.json").write_text(json.dumps({"window": DATA["window"]}), encoding="utf-8")
    body = _cli(run, "email").read_text(encoding="utf-8")
    assert "The latest I&amp;O project status report is on SharePoint:" in body and "Spending report" in body


def test_cli_collect(output):
    run = output / "IOProjectLeadershipUpdates_20261106_1100"
    cli.main(["leadership-collect", str(run), "--from", "2026-10-30T00:00:00-04:00", "--to", "2026-11-06T12:00:00-05:00"])
    digest = json.loads((run / "reports.json").read_text(encoding="utf-8"))
    assert len(digest["runs"]) == 2 and digest["projects"][3]["deck_name"] == "Rubrik"
    with pytest.raises(SystemExit):
        cli.main(["leadership-collect", str(run)])  # --from and --to are required
