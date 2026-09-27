"""결과지에 참고치가 있고, 그 줄을 맡는 다른 부품이 없을 때 씁니다."""

from __future__ import annotations

from examkit.analyzer import Analyzer
from examkit.models import Finding, Result, Severity, Status, Subject, reference_text
from examkit.normalize import format_number


class PrintedReferenceAnalyzer(Analyzer):
    id = "printed_reference"
    description = "맡은 부품이 없는 혈액검사 항목을 결과지의 참고치와 대조합니다."
    fallback = True

    def matches(self, result: Result) -> bool:
        return result.has_reference or bool(result.flag)

    def analyze_result(self, result: Result, subject: Subject) -> list[Finding]:
        status = _status(result)
        if status is None:
            return []
        label = result.label
        value = format_number(result.value)
        unit = f" {result.unit}" if result.unit else ""
        shown = reference_text(result)
        if status is Status.LOW and shown:
            title = f"결과지 참고치보다 낮음: {label}"
            summary = f"{label} {value}{unit}. 결과지 참고치 {shown}보다 낮습니다."
        elif status is Status.HIGH and shown:
            title = f"결과지 참고치보다 높음: {label}"
            summary = f"{label} {value}{unit}. 결과지 참고치 {shown}보다 높습니다."
        elif status is Status.NORMAL and shown:
            title = f"결과지 참고치 안: {label}"
            summary = f"{label} {value}{unit}. 결과지 참고치 {shown} 안에 있습니다."
        elif status is Status.LOW:
            title = f"결과지에 낮음으로 표시: {label}"
            summary = f"{label} {value}{unit}. 결과지에 낮은 쪽으로 표시되어 있습니다."
        else:
            title = f"결과지에 높음으로 표시: {label}"
            summary = f"{label} {value}{unit}. 결과지에 높은 쪽으로 표시되어 있습니다."
        severity = Severity.INFO if status is Status.NORMAL else Severity.ATTENTION
        return [
            Finding(
                analyzer_id=self.id,
                status=status,
                severity=severity,
                title=title,
                summary=summary,
                codes=(result.code,),
                evidence={
                    "reference_low": result.reference_low,
                    "reference_high": result.reference_high,
                    "flag": result.flag,
                },
            )
        ]


def _status(result: Result) -> Status | None:
    if result.has_reference:
        if _below(result):
            return Status.LOW
        if _above(result):
            return Status.HIGH
        return Status.NORMAL
    if result.flag == "L":
        return Status.LOW
    if result.flag == "H":
        return Status.HIGH
    return None


def _below(result: Result) -> bool:
    if result.reference_low is None:
        return False
    if result.reference_low_inclusive:
        return result.value < result.reference_low
    return result.value <= result.reference_low


def _above(result: Result) -> bool:
    if result.reference_high is None:
        return False
    if result.reference_high_inclusive:
        return result.value > result.reference_high
    return result.value >= result.reference_high
