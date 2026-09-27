"""헤모글로빈 한 항목. 성별에 따라 구간이 달라집니다."""

from __future__ import annotations

from typing import ClassVar

from examkit.models import Severity, Sex, Status
from examkit.ranges import Band, RangeAnalyzer


def _urgent() -> Band:
    return Band(
        upper=8,
        inclusive=False,
        status=Status.LOW,
        severity=Severity.URGENT,
        title="헤모글로빈이 매우 낮은 구간",
        summary=(
            "헤모글로빈이 {value} {unit}입니다. "
            "8 g/dL 미만은 이 부품에서 많이 낮은 값으로 표시합니다."
        ),
    )


class HemoglobinAnalyzer(RangeAnalyzer):
    id = "hemoglobin"
    description = "헤모글로빈 한 항목을 성별이 있는 성인 참고 구간과 대조합니다."
    codes = ("HGB", "HB", "HEMOGLOBIN")
    names = ("헤모글로빈", "혈색소", "hemoglobin")
    expected_unit = "g/dL"
    conversions: ClassVar[dict[str, float]] = {"g/L": 0.1}
    bands_by_sex = {
        Sex.FEMALE: (
            _urgent(),
            Band(
                upper=12,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 낮은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "성인 여성에서 12 g/dL 미만은 낮은 구간으로 보는 기준이 많습니다."
                ),
            ),
            Band(
                upper=15.5,
                inclusive=True,
                status=Status.NORMAL,
                severity=Severity.INFO,
                title="헤모글로빈 참고 구간 안",
                summary=(
                    "헤모글로빈이 {value} {unit}로, "
                    "이 부품의 성인 여성 참고 구간(12–15.5 g/dL) 안에 있습니다."
                ),
            ),
            Band(
                upper=None,
                inclusive=False,
                status=Status.HIGH,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 높은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "이 부품은 성인 여성에서 15.5 g/dL를 넘으면 높은 구간으로 둡니다."
                ),
            ),
        ),
        Sex.MALE: (
            _urgent(),
            Band(
                upper=13,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 낮은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "성인 남성에서 13 g/dL 미만은 낮은 구간으로 보는 기준이 많습니다."
                ),
            ),
            Band(
                upper=17.5,
                inclusive=True,
                status=Status.NORMAL,
                severity=Severity.INFO,
                title="헤모글로빈 참고 구간 안",
                summary=(
                    "헤모글로빈이 {value} {unit}로, "
                    "이 부품의 성인 남성 참고 구간(13–17.5 g/dL) 안에 있습니다."
                ),
            ),
            Band(
                upper=None,
                inclusive=False,
                status=Status.HIGH,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 높은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "이 부품은 성인 남성에서 17.5 g/dL를 넘으면 높은 구간으로 둡니다."
                ),
            ),
        ),
        Sex.UNKNOWN: (
            _urgent(),
            Band(
                upper=12,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 낮은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "12 g/dL 미만은 성인 여성과 남성 기준 모두에서 낮은 구간입니다."
                ),
            ),
            Band(
                upper=13,
                inclusive=False,
                status=Status.BORDERLINE,
                severity=Severity.ATTENTION,
                title="헤모글로빈 경계 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "12 이상 13 g/dL 미만은 여성 기준으로는 참고 구간 안이고, "
                    "남성 기준으로는 낮은 구간입니다. 성별이 없어 경계로 두었습니다."
                ),
            ),
            Band(
                upper=15.5,
                inclusive=True,
                status=Status.NORMAL,
                severity=Severity.INFO,
                title="헤모글로빈 참고 구간 안",
                summary=(
                    "헤모글로빈이 {value} {unit}로, "
                    "성별이 없어도 양쪽 참고 구간이 겹치는 13–15.5 g/dL 안에 있습니다."
                ),
            ),
            Band(
                upper=17.5,
                inclusive=True,
                status=Status.BORDERLINE,
                severity=Severity.ATTENTION,
                title="헤모글로빈 경계 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "15.5 g/dL를 넘고 17.5 g/dL 이하인 값은 남성 기준으로는 참고 구간 안일 수 있습니다. "
                    "성별이 없어 경계로 두었습니다."
                ),
            ),
            Band(
                upper=None,
                inclusive=False,
                status=Status.HIGH,
                severity=Severity.ATTENTION,
                title="헤모글로빈이 높은 구간",
                summary=(
                    "헤모글로빈이 {value} {unit}입니다. "
                    "17.5 g/dL를 넘는 값은 성별과 관계없이 이 부품의 높은 구간입니다."
                ),
            ),
        ),
    }
