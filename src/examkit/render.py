"""해석 결과를 글과 JSON으로 내보냅니다."""

from __future__ import annotations

from typing import Any

from examkit.models import Finding, Report, Severity
from examkit.normalize import format_number
from examkit.registry import AnalyzerSpec

DISCLAIMER = (
    "이 결과는 등록된 분석 부품이 참고 구간과 대조한 설명입니다. "
    "진단, 치료, 복용 결정을 대신하지 않습니다."
)

_SEVERITY_LABEL = {
    Severity.URGENT: "확인 필요",
    Severity.ATTENTION: "주의",
    Severity.INFO: "참고",
}

_SEVERITY_RANK = {
    Severity.URGENT: 0,
    Severity.ATTENTION: 1,
    Severity.INFO: 2,
}

_SEX_LABEL = {
    "female": "여성",
    "male": "남성",
    "unknown": "성별 미상",
}


def render_report(report: Report) -> str:
    lines = ["검사 결과 해석", _subject_line(report), ""]
    if not report.findings and not report.unhandled:
        lines.append("해석할 검사 항목이 없습니다.")
        lines.append("")
    for finding in _display_findings(report):
        lines.append(f"[{_SEVERITY_LABEL[finding.severity]}] {finding.title}")
        lines.append(finding.summary)
        lines.append(f"부품: {finding.analyzer_id}")
        lines.append("")
    if report.unhandled:
        lines.append("등록된 부품이 없는 항목")
        for result in report.unhandled:
            unit = f" {result.unit}" if result.unit else ""
            label = result.name or result.code
            lines.append(f"- {label}: {format_number(result.value)}{unit} ({result.code})")
        lines.append("")
    lines.append(DISCLAIMER)
    return "\n".join(lines).rstrip() + "\n"


def report_to_dict(report: Report) -> dict[str, Any]:
    subject: dict[str, Any] = {"sex": report.subject.sex.value}
    if report.subject.age_years is not None:
        subject["age_years"] = report.subject.age_years
    return {
        "subject": subject,
        "findings": [
            {
                "analyzer_id": finding.analyzer_id,
                "status": finding.status.value,
                "severity": finding.severity.value,
                "title": finding.title,
                "summary": finding.summary,
                "codes": list(finding.codes),
                "evidence": dict(finding.evidence),
            }
            for finding in report.findings
        ],
        "unhandled": [
            {
                "code": result.code,
                "name": result.name,
                "value": result.value,
                "unit": result.unit,
            }
            for result in report.unhandled
        ],
        "disclaimer": DISCLAIMER,
    }


def format_catalog(specs: tuple[AnalyzerSpec, ...]) -> str:
    lines: list[str] = []
    for spec in specs:
        state = "켜짐" if spec.enabled else "꺼짐"
        if spec.scope == "result":
            extra = "코드: " + ", ".join(spec.codes)
        elif spec.uses:
            extra = "사용: " + ", ".join(spec.uses)
        else:
            extra = "패널"
        lines.append(f"{spec.id}\t{spec.scope}\t{state}\t{extra}")
        if spec.description:
            lines.append(f"  {spec.description}")
    if not lines:
        return "등록된 부품이 없습니다.\n"
    return "\n".join(lines) + "\n"


def _subject_line(report: Report) -> str:
    sex = _SEX_LABEL[report.subject.sex.value]
    if report.subject.age_years is None:
        return f"대상: {sex}"
    return f"대상: {sex}, {format_number(report.subject.age_years)}세"


def _display_findings(report: Report) -> list[Finding]:
    ranked = sorted(
        enumerate(report.findings),
        key=lambda item: (_SEVERITY_RANK[item[1].severity], item[0]),
    )
    return [finding for _, finding in ranked]
