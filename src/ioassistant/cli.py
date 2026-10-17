"""Command line: python -m ioassistant.cli {report,spend} <json-file>."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import report, spend


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(prog="ioassistant")
    ap.add_argument("command", choices=["report", "spend"])
    ap.add_argument("path", type=Path)
    ap.add_argument("--no-fonts", action="store_true", help="spend only: skip embedded brand fonts (small file)")
    args = ap.parse_args(argv)
    if args.command == "spend":
        out = spend.build(args.path, fonts=not args.no_fonts)
    else:
        out = report.build(args.path)
    print(out)


if __name__ == "__main__":
    main()
