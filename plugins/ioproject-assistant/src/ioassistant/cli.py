"""Command line: python -m ioassistant.cli {report,spend,confluence,email,presentation,sprint-changes,sprint-tickets} <json-file>."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import confluence, emaildraft, presentation, report, spend, sprintchanges, sprinttickets


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="ioassistant")
    ap.add_argument("command", choices=["report", "spend", "confluence", "email", "presentation", "sprint-changes", "sprint-tickets"])
    ap.add_argument("path", type=Path, nargs="?", help="data/usage json (not needed for presentation)")
    ap.add_argument("--compact", action="store_true",
                    help="write to <run>/upload/ without embedded fonts and with a small logo (fits one connector upload)")
    ap.add_argument("--orchestrator-tokens", type=int, metavar="N",
                    help="spend: total tokens of the orchestrator's Agent result, written into usage.json before rendering")
    ap.add_argument("--orchestrator-seconds", type=float, metavar="S",
                    help="spend: orchestrator duration in seconds (default: keep the recorded wall-clock)")
    ap.add_argument("--orchestrator-row", default="orchestrator", metavar="NAME",
                    help='spend: usage.json row to fill with --orchestrator-tokens (a resume run uses "orchestrator (resume)")')
    args = ap.parse_args(argv)
    if args.command == "presentation":
        out = presentation.build()
    elif args.path is None:
        ap.error("path is required for this command")
    elif args.command == "sprint-changes":
        out = sprintchanges.build(args.path)
    elif args.command == "sprint-tickets":
        out = sprinttickets.build(args.path)
    elif args.command == "spend":
        if args.orchestrator_tokens is not None:
            spend.set_orchestrator(args.path, args.orchestrator_tokens, args.orchestrator_seconds, args.orchestrator_row)
        out = spend.build(args.path, compact=args.compact)
    elif args.command == "confluence":
        out = confluence.build(args.path)
    elif args.command == "email":
        out = emaildraft.build(args.path)
    else:
        out = report.build(args.path, compact=args.compact)
    print(out)


if __name__ == "__main__":
    main()
