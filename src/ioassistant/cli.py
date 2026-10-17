"""Command line: python -m ioassistant.cli {report,spend,confluence,email} <json-file>."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import confluence, emaildraft, report, spend


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="ioassistant")
    ap.add_argument("command", choices=["report", "spend", "confluence", "email"])
    ap.add_argument("path", type=Path)
    ap.add_argument("--compact", action="store_true",
                    help="write to <run>/upload/ without embedded fonts and with a small logo (fits one connector upload)")
    args = ap.parse_args(argv)
    if args.command == "spend":
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
