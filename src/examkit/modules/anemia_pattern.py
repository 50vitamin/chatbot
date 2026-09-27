"""헤모글로빈 부품과 영양 부품의 상태를 모아 같이 낮은 패턴만 설명합니다.

원본 숫자를 다시 해석하지 않습니다. 앞 부품이 남긴 Status가 소켓입니다.
페리틴 부품을 빼면 철 결핍 패턴은 말하지 않습니다.
"""

from __future__ import annotations

from collections.abc import Sequence

from examkit.analyzer import Analyzer
from examkit.models import Finding, Panel, Severity, Status, adult_range_note

HEMOGLOBIN = "hemoglobin"
FERRITIN = "ferritin"
VITAMIN_B12 = "vitamin_b12"


class AnemiaPatternAnalyzer(Analyzer):
    id = "anemia_pattern"
    description = "헤모글로빈, 페리틴, 비타민 B12 부품의 해석을 모아 같이 낮은 패턴만 설명합니다."
    scope = "panel"
    uses = (HEMOGLOBIN, FERRITIN, VITAMIN_B12)

    def analyze_panel(self, panel: Panel, findings: Sequence[Finding]) -> list[Finding]:
        if _status(findings, HEMOGLOBIN) is not Status.LOW:
            return []
        iron = _status(findings, FERRITIN) is Status.LOW
        b12 = _status(findings, VITAMIN_B12) is Status.LOW
        if not iron and not b12:
            return []
        based_on = [HEMOGLOBIN]
        if iron and b12:
            title = "헤모글로빈, 페리틴, 비타민 B12가 함께 낮은 패턴"
            summary = (
                "헤모글로빈, 페리틴, 비타민 B12 부품이 모두 낮은 구간입니다. "
                "철이 낮은 패턴과 비타민 B12가 낮은 패턴이 같이 보여, 한 원인으로 단정하기 어렵습니다."
            )
            based_on.extend([FERRITIN, VITAMIN_B12])
        elif iron:
            title = "헤모글로빈과 페리틴이 함께 낮은 패턴"
            summary = (
                "헤모글로빈과 페리틴 부품이 모두 낮은 구간입니다. "
                "철이 부족한 빈혈 패턴과 맞는 조합으로 자주 설명됩니다. "
                "각 항목의 단독 해석은 해당 부품 결과를 보세요."
            )
            based_on.append(FERRITIN)
        else:
            title = "헤모글로빈과 비타민 B12가 함께 낮은 패턴"
            summary = (
                "헤모글로빈과 비타민 B12 부품이 모두 낮은 구간입니다. "
                "비타민 B12가 낮은 빈혈 패턴과 맞는 조합으로 자주 설명됩니다. "
                "각 항목의 단독 해석은 해당 부품 결과를 보세요."
            )
            based_on.append(VITAMIN_B12)
        summary += adult_range_note(panel.subject)
        codes: list[str] = []
        for finding in findings:
            if finding.analyzer_id in based_on:
                codes.extend(finding.codes)
        return [
            Finding(
                analyzer_id=self.id,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title=title,
                summary=summary,
                codes=tuple(codes),
                evidence={"based_on": based_on},
            )
        ]


def _status(findings: Sequence[Finding], analyzer_id: str) -> Status | None:
    for finding in findings:
        if finding.analyzer_id == analyzer_id and finding.status is not Status.UNKNOWN:
            return finding.status
    return None
