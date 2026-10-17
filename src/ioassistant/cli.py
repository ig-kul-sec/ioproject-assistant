"""Command line: python -m ioassistant.cli {report,spend} <json-file>."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import report, spend


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="ioassistant")
    ap.add_argument("command", choices=["report", "spend"])
    ap.add_argument("path", type=Path)
    args = ap.parse_args(argv)
    out = (report.build if args.command == "report" else spend.build)(args.path)
    print(out)


if __name__ == "__main__":
    main()
