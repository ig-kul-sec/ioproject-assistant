"""Sum the real token usage of one agent from its Claude Code transcript (JSONL).

Spike for a SubagentStop hook: the hook gets the subagent's transcript path and appends this row to usage.json,
so no model has to report (or guess) its own tokens.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path

FIELDS = ("input_tokens", "output_tokens", "cache_read_input_tokens", "cache_creation_input_tokens")


def _ts(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def summarize(path: Path, agent: str = "") -> dict:
    """One usage row. A streamed API response is written to the transcript several times with the same
    message id, so keep only the last usage per message id (counting every line would roughly double the totals)."""
    usage: dict[str, dict] = {}
    models: Counter = Counter()
    stamps: list[datetime] = []
    for line in Path(path).read_text(encoding="utf-8").splitlines():
        try:
            entry = json.loads(line)
        except ValueError:
            continue
        if entry.get("timestamp"):
            stamps.append(_ts(entry["timestamp"]))
        message = entry.get("message") or {}
        if isinstance(message.get("usage"), dict):
            key = message.get("id") or entry.get("requestId") or entry.get("uuid")
            usage[key] = message["usage"]
            models[message.get("model")] += 1
    totals = {f: sum(int(u.get(f) or 0) for u in usage.values()) for f in FIELDS}
    return {
        "agent": agent,
        "model": models.most_common(1)[0][0] if models else None,
        "input_tokens": totals["input_tokens"],
        "output_tokens": totals["output_tokens"],
        "cache_read_tokens": totals["cache_read_input_tokens"],
        "cache_write_tokens": totals["cache_creation_input_tokens"],
        "api_calls": len(usage),
        "seconds": round((max(stamps) - min(stamps)).total_seconds(), 1) if stamps else 0.0,
        "note": "from transcript usage (measured)",
    }


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="transcript_usage")
    ap.add_argument("path", type=Path)
    ap.add_argument("--agent", default="")
    args = ap.parse_args(argv)
    print(json.dumps(summarize(args.path, args.agent), indent=1))


if __name__ == "__main__":
    main()
