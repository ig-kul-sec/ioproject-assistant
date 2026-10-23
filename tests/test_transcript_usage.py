import json

from ioassistant import transcript_usage


def _line(ts, msg_id=None, model=None, usage=None):
    entry = {"timestamp": ts, "message": {}}
    if msg_id:
        entry["message"] = {"id": msg_id, "model": model, "usage": usage}
    return json.dumps(entry)


def test_summarize_counts_each_message_once_and_measures_seconds(tmp_path):
    first = {"input_tokens": 5, "output_tokens": 1, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10}
    final = {"input_tokens": 5, "output_tokens": 40, "cache_read_input_tokens": 100, "cache_creation_input_tokens": 10}
    other = {"input_tokens": 2, "output_tokens": 8, "cache_read_input_tokens": 50, "cache_creation_input_tokens": 0}
    path = tmp_path / "agent.jsonl"
    path.write_text("\n".join([
        _line("2026-10-22T14:00:00.000Z"),
        _line("2026-10-22T14:00:05.000Z", "m1", "claude-sonnet-5-5", first),  # streamed twice: the last one wins
        _line("2026-10-22T14:00:06.000Z", "m1", "claude-sonnet-5-5", final),
        "not json",
        _line("2026-10-22T14:01:30.500Z", "m2", "claude-sonnet-5-5", other),
    ]), encoding="utf-8")
    row = transcript_usage.summarize(path, "teams-collector")
    assert row["agent"] == "teams-collector" and row["model"] == "claude-sonnet-5-5"
    assert (row["input_tokens"], row["output_tokens"]) == (7, 48)
    assert (row["cache_read_tokens"], row["cache_write_tokens"], row["api_calls"]) == (150, 10, 2)
    assert row["seconds"] == 90.5


def test_summarize_empty_transcript(tmp_path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    row = transcript_usage.summarize(path)
    assert row["model"] is None and row["api_calls"] == 0 and row["seconds"] == 0.0
