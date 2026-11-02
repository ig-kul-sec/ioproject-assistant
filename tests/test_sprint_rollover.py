"""The current sprint follows the report day, not only Jira's "active" state (a sprint that has ended can stay active)."""
import json
from datetime import date

import pytest

from ioassistant import sprintchanges, sprinttickets

TODAY = date(2026, 11, 2)


def _data(**over):
    base = {"window": {"from": "2026-10-30T00:00:00-04:00", "to": "2026-11-02T10:58:28-05:00"},
            "sprint": {"id": 376, "name": "I&O 26.44", "start": "2026-10-26", "end": "2026-10-30",
                       "tickets": [{"key": "COR-1"}]},
            "gaps": []}
    base.update(over)
    return base


def _board(*extra):
    return [{"id": 376, "name": "I&O 26.44", "state": "active",
             "startDate": "2026-10-26T13:00:00.000Z", "endDate": "2026-10-30T21:00:00.000Z"}, *extra]


NEXT = {"id": 377, "name": "I&O 26.45", "state": "future",
        "startDate": "2026-11-02T14:00:00.000Z", "endDate": "2026-11-06T22:00:00.000Z"}


def test_ended_active_sprint_becomes_past_and_next_sprint_is_current():
    data = _data()
    note = sprinttickets.roll_over(data, _board(NEXT), TODAY)
    assert data["sprint"]["id"] == 377 and data["sprint"]["name"] == "I&O 26.45"
    assert (data["sprint"]["start"], data["sprint"]["end"]) == ("2026-11-02", "2026-11-06")
    assert [p["name"] for p in data["past_sprints"]] == ["I&O 26.44"]
    assert data["past_sprints"][0]["tickets"] == [{"key": "COR-1"}]  # what the collector read is kept
    assert "I&O 26.44" in note and "I&O 26.45" in note and "still active" in note


def test_sprint_that_covers_the_report_day_stays_current():
    data = _data(sprint={"id": 376, "name": "I&O 26.44", "start": "2026-10-26", "end": "2026-11-02"})
    assert sprinttickets.roll_over(data, _board(NEXT), TODAY) is None
    assert data["sprint"]["name"] == "I&O 26.44" and "past_sprints" not in data


def test_no_later_sprint_leaves_the_data_alone():
    data = _data()
    assert sprinttickets.roll_over(data, _board(), TODAY) is None
    assert data["sprint"]["name"] == "I&O 26.44"


def test_earliest_future_sprint_wins_and_closed_ones_are_ignored():
    later = {"id": 378, "name": "I&O 26.46", "state": "future",
             "startDate": "2026-11-09T14:00:00.000Z", "endDate": "2026-11-13T22:00:00.000Z"}
    closed = {"id": 370, "name": "I&O 26.43", "state": "closed",
              "startDate": "2026-10-19T13:00:00.000Z", "endDate": "2026-10-23T21:00:00.000Z"}
    old_active = {"id": 371, "name": "I&O 26.42", "state": "active",
                  "startDate": "2026-10-12T13:00:00.000Z", "endDate": "2026-10-16T21:00:00.000Z"}
    data = _data(past_sprints=[{"id": 371, "name": "I&O 26.42", "tickets": []}])
    sprinttickets.roll_over(data, _board(later, NEXT, closed, old_active), TODAY)
    assert data["sprint"]["name"] == "I&O 26.45"
    assert [p["name"] for p in data["past_sprints"]] == ["I&O 26.42", "I&O 26.44"]


def test_future_sprint_without_dates_gets_dates_from_the_previous_sprint_and_says_so():
    undated = {"id": 377, "name": "I&O 26.45", "state": "future"}
    data = _data()
    note = sprinttickets.roll_over(data, _board(undated), TODAY)
    assert (data["sprint"]["start"], data["sprint"]["end"]) == ("2026-11-02", "2026-11-06")
    assert "dates" in note and "assumed" in note


def test_sprint_without_an_end_date_is_never_rolled_over():
    data = _data(sprint={"id": 376, "name": "I&O 26.44", "start": "2026-10-26"})
    assert sprinttickets.roll_over(data, _board(NEXT), TODAY) is None


def test_build_writes_the_rolled_over_sprint_with_its_full_ticket_list(tmp_path, monkeypatch):
    path = tmp_path / "data.json"
    path.write_text(json.dumps(_data()), encoding="utf-8")
    monkeypatch.setattr(sprinttickets, "_token", lambda: "t")
    monkeypatch.setattr(sprinttickets, "board_sprints", lambda site, token, states="active": _board(NEXT))
    fetched = []
    monkeypatch.setattr(sprinttickets, "fetch",
                        lambda site, sid, token: fetched.append(sid) or [{"key": f"IOSP-{sid}", "fields": {}}])
    sprinttickets.build(path)
    out = json.loads(path.read_text(encoding="utf-8"))
    assert out["sprint"]["name"] == "I&O 26.45" and out["sprint"]["tickets"][0]["key"] == "IOSP-377"
    assert [p["name"] for p in out["past_sprints"]] == ["I&O 26.44"]
    assert out["past_sprints"][0]["tickets"][0]["key"] == "IOSP-376"
    assert fetched == [377, 376] and any("I&O 26.45" in g for g in out["gaps"])


def test_board_sprints_pages_until_the_last_page(monkeypatch):
    pages = [{"values": [{"id": 1}, {"id": 2}], "isLast": False}, {"values": [{"id": 3}], "isLast": True}]
    seen = []
    monkeypatch.setattr(sprintchanges, "_get", lambda site, path, params, token: seen.append(params) or pages[len(seen) - 1])
    assert [s["id"] for s in sprintchanges.board_sprints("https://j", "t", "active,future")] == [1, 2, 3]
    assert seen[0]["state"] == "active,future" and seen[1]["startAt"] == 2


def test_sprint_changes_can_read_a_sprint_that_has_not_started(monkeypatch):
    monkeypatch.setattr(sprintchanges, "_token", lambda: "t")
    monkeypatch.setattr(sprintchanges, "board_sprints", lambda site, token, states="active": [NEXT])
    monkeypatch.setattr(sprintchanges, "_get", lambda site, path, params, token: {"issues": []})
    assert sprintchanges.fetch("https://j", "I&O 26.45", "2026-11-02") == []
    with pytest.raises(SystemExit):
        sprintchanges.fetch("https://j", "I&O 26.99", "2026-11-02")
