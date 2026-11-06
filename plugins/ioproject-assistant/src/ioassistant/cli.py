"""Command line: python -m ioassistant.cli {report,spend,confluence,email,presentation,sprint-changes,sprint-tickets,release-log,leadership-collect,leadership-report} <json-file>."""
from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path

from . import confluence, emaildraft, leadership, presentation, releaselog, report, spend, sprintchanges, sprinttickets


def _when(text: str) -> datetime:
    """ISO timestamp; one without an offset is read as America/New_York."""
    try:
        when = datetime.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO timestamp: {text}")
    return when if when.tzinfo else when.replace(tzinfo=leadership.TZ)


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="ioassistant")
    ap.add_argument("command", choices=["report", "spend", "confluence", "email", "presentation", "sprint-changes", "sprint-tickets", "release-log",
                                        "leadership-collect", "leadership-report"])
    ap.add_argument("path", type=Path, nargs="?",
                    help="data/usage json (CHANGELOG.md for release-log; the run folder for leadership-collect; not needed for presentation)")
    ap.add_argument("--from", dest="window_from", type=_when, metavar="ISO", help="leadership-collect: start of the analysis period")
    ap.add_argument("--to", dest="window_to", type=_when, metavar="ISO", help="leadership-collect: end of the analysis period")
    ap.add_argument("--page-body", type=Path, metavar="FILE",
                    help="release-log: current Confluence page body (storage format); the RELEASE LOG section is merged into it")
    ap.add_argument("--out", type=Path, metavar="FILE", help="release-log: output file (default output/release-log/...)")
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
    elif args.command == "release-log":
        out = releaselog.build(args.path, args.page_body, args.out)
    elif args.command == "sprint-changes":
        out = sprintchanges.build(args.path)
    elif args.command == "sprint-tickets":
        out = sprinttickets.build(args.path)
    elif args.command == "spend":
        if args.orchestrator_tokens is not None:
            spend.set_orchestrator(args.path, args.orchestrator_tokens, args.orchestrator_seconds, args.orchestrator_row)
        out = spend.build(args.path, compact=args.compact)
    elif args.command == "leadership-collect":
        if not (args.window_from and args.window_to):
            ap.error("leadership-collect needs --from and --to")
        out = leadership.collect_to(args.path, args.window_from, args.window_to)
    elif args.command == "leadership-report":
        out = leadership.build(args.path, compact=args.compact)
    elif args.command == "confluence":  # leadership runs share the skills, so the run folder name picks the content
        out = leadership.build_body(args.path, confluence=True) if leadership.is_leadership(args.path.parent.name) else confluence.build(args.path)
    elif args.command == "email":
        out = leadership.build_body(args.path) if leadership.is_leadership(args.path.parent.name) else emaildraft.build(args.path)
    else:
        out = report.build(args.path, compact=args.compact)
    print(out)


if __name__ == "__main__":
    main()
