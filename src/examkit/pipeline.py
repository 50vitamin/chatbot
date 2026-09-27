"""등록된 부품만 순서대로 실행합니다. 혈액검사 항목 이름은 여기서 모릅니다."""

from __future__ import annotations

from examkit.analyzer import Analyzer
from examkit.models import Finding, Panel, Report, Result, Severity, Status
from examkit.registry import Registry


class Pipeline:
    def __init__(self, registry: Registry | None = None) -> None:
        self.registry = registry if registry is not None else Registry.discover()

    @classmethod
    def discover(cls) -> Pipeline:
        return cls(Registry.discover())

    def run(self, panel: Panel) -> Report:
        findings: list[Finding] = []
        handled: set[int] = set()
        result_parts = sorted(
            (part for part in self.registry.enabled() if part.scope == "result"),
            key=lambda part: part.id,
        )
        panel_parts = sorted(
            (part for part in self.registry.enabled() if part.scope == "panel"),
            key=lambda part: part.id,
        )
        dedicated = [part for part in result_parts if not part.fallback]
        fallbacks = [part for part in result_parts if part.fallback]

        for index, result in enumerate(panel.results):
            matched = [part for part in dedicated if part.matches(result)]
            if not matched:
                matched = [part for part in fallbacks if part.matches(result)]
            if matched:
                handled.add(index)
            for part in matched:
                findings.extend(_run_result(part, result, panel))

        for part in panel_parts:
            findings.extend(_run_panel(part, panel, tuple(findings)))

        unhandled = tuple(result for index, result in enumerate(panel.results) if index not in handled)
        return Report(findings=tuple(findings), unhandled=unhandled, subject=panel.subject)


def _run_result(part: Analyzer, result: Result, panel: Panel) -> list[Finding]:
    try:
        produced = part.analyze_result(result, panel.subject)
    except Exception as exc:
        return [_part_error(part, (result.code,), exc)]
    return list(produced)


def _run_panel(part: Analyzer, panel: Panel, findings: tuple[Finding, ...]) -> list[Finding]:
    try:
        produced = part.analyze_panel(panel, findings)
    except Exception as exc:
        codes = tuple(result.code for result in panel.results)
        return [_part_error(part, codes, exc)]
    return list(produced)


def _part_error(part: Analyzer, codes: tuple[str, ...], exc: Exception) -> Finding:
    return Finding(
        analyzer_id=part.id,
        status=Status.UNKNOWN,
        severity=Severity.ATTENTION,
        title="분석 부품 오류",
        summary=f"{part.id} 부품을 실행하지 못했습니다: {exc}",
        codes=codes,
        evidence={"error_type": type(exc).__name__},
    )
