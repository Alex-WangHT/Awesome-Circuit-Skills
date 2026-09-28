"""Validate IR and export deterministic EDA artifacts."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .adapters.kicad import KiCadAdapter
from .validation import validate


ADAPTERS = {"kicad": KiCadAdapter}


def _reject_constant(token: str) -> None:
    raise ValueError(f"Non-finite JSON number: {token}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="circuit_skills")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("validate", help="validate a Component or Architecture IR file")
    check.add_argument("input", type=Path)
    export = sub.add_parser("export", help="validate and export EDA artifacts")
    export.add_argument("input", type=Path)
    export.add_argument("--eda", choices=ADAPTERS, default="kicad")
    export.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        ir = json.loads(args.input.read_text(encoding="utf-8"), parse_constant=_reject_constant)
    except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as exc:
        print(f"Cannot read IR: {exc}", file=sys.stderr)
        return 2
    report = validate(ir)
    if args.command == "validate":
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return 1 if report["status"] == "FAIL" else 0
    if report["status"] == "FAIL":
        print(json.dumps(report, indent=2, ensure_ascii=False), file=sys.stderr)
        return 1
    try:
        adapter = ADAPTERS[args.eda]()
        if ir["kind"] == "component":
            paths = adapter.export_component(ir, args.out)
        else:
            paths = adapter.export_architecture(ir, args.out)
        report_path = args.out / "verification.json"
        report_path.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        paths.append(report_path)
    except (OSError, KeyError, TypeError, ValueError) as exc:
        print(f"Export failed: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"status": report["status"], "files": [str(p) for p in paths]}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
