"""명령줄에서 부품 목록과 패널 해석을 실행합니다."""

from __future__ import annotations

import argparse
import json
import sys

from examkit.parse import ParseError, load_panel, loads_panel
from examkit.pipeline import Pipeline
from examkit.registry import Registry
from examkit.render import format_catalog


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="examkit",
        description="혈액검사 결과 분석 부품을 끼워 실행하는 베이스 프로그램",
    )
    commands = parser.add_subparsers(dest="command", required=True)

    report = commands.add_parser("report", help="혈액검사 결과지를 해석합니다")
    report.add_argument("path", help="JSON 또는 텍스트 패널 파일")
    report.add_argument("--json", action="store_true", help="JSON으로 출력합니다")

    commands.add_parser("parts", help="끼워진 분석 부품을 나열합니다")

    args = parser.parse_args(argv)
    registry = Registry.discover()
    if args.command == "parts":
        sys.stdout.write(format_catalog(registry.specs()))
        return 0

    try:
        if args.path == "-":
            panel = loads_panel(sys.stdin.read(), registry)
        else:
            panel = load_panel(args.path, registry)
    except (OSError, ParseError, ValueError) as exc:
        sys.stderr.write(f"{exc}\n")
        return 2
    report_data = Pipeline(registry).run(panel)
    if args.json:
        json.dump(report_data.to_dict(), sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(report_data.to_text())
    return 0
