"""페리틴 한 항목. 성별에 따라 구간이 달라집니다."""

from __future__ import annotations

from typing import ClassVar

from examkit.models import Severity, Sex, Status
from examkit.ranges import Band, RangeAnalyzer


def _normal(summary: str, upper: float) -> Band:
    return Band(
        upper=upper,
        inclusive=True,
        status=Status.NORMAL,
        severity=Severity.INFO,
        title="페리틴 참고 구간 안",
        summary=summary,
    )


def _high(summary: str) -> Band:
    return Band(
        upper=None,
        inclusive=False,
        status=Status.HIGH,
        severity=Severity.ATTENTION,
        title="페리틴이 높은 구간",
        summary=summary,
    )


def _borderline(upper: float, summary: str) -> Band:
    return Band(
        upper=upper,
        inclusive=False,
        status=Status.BORDERLINE,
        severity=Severity.ATTENTION,
        title="페리틴 경계 구간",
        summary=summary,
    )


class FerritinAnalyzer(RangeAnalyzer):
    id = "ferritin"
    description = "페리틴 한 항목을 성별이 있는 성인 참고 구간과 대조합니다."
    codes = ("FERRITIN", "FERR")
    names = ("페리틴", "ferritin")
    expected_unit = "ng/mL"
    conversions: ClassVar[dict[str, float]] = {"ug/L": 1.0, "µg/L": 1.0}
    bands_by_sex = {
        Sex.FEMALE: (
            Band(
                upper=15,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="페리틴이 낮은 구간",
                summary=(
                    "페리틴이 {value} {unit}입니다. "
                    "성인 여성에서 15 ng/mL 미만은 낮은 구간으로 자주 봅니다."
                ),
            ),
            _normal(
                "페리틴이 {value} {unit}로, 이 부품의 성인 여성 참고 구간(15–150 ng/mL) 안에 있습니다.",
                150,
            ),
            _high(
                "페리틴이 {value} {unit}입니다. "
                "이 부품은 성인 여성에서 150 ng/mL를 넘으면 높은 구간으로 둡니다."
            ),
        ),
        Sex.MALE: (
            Band(
                upper=30,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="페리틴이 낮은 구간",
                summary=(
                    "페리틴이 {value} {unit}입니다. "
                    "성인 남성에서 30 ng/mL 미만은 낮은 구간으로 자주 봅니다."
                ),
            ),
            _normal(
                "페리틴이 {value} {unit}로, 이 부품의 성인 남성 참고 구간(30–400 ng/mL) 안에 있습니다.",
                400,
            ),
            _high(
                "페리틴이 {value} {unit}입니다. "
                "이 부품은 성인 남성에서 400 ng/mL를 넘으면 높은 구간으로 둡니다."
            ),
        ),
        Sex.UNKNOWN: (
            Band(
                upper=15,
                inclusive=False,
                status=Status.LOW,
                severity=Severity.ATTENTION,
                title="페리틴이 낮은 구간",
                summary=(
                    "페리틴이 {value} {unit}입니다. "
                    "성별과 관계없이 15 ng/mL 미만은 낮은 구간으로 자주 봅니다."
                ),
            ),
            _borderline(
                30,
                "페리틴이 {value} {unit}입니다. "
                "15 이상 30 ng/mL 미만은 여성 기준으로는 참고 구간 안이고, "
                "남성 기준으로는 낮은 구간입니다. 성별이 없어 경계로 두었습니다.",
            ),
            _normal(
                "페리틴이 {value} {unit}로, 성별이 없어도 양쪽 참고 구간이 겹치는 30–150 ng/mL 안에 있습니다.",
                150,
            ),
            Band(
                upper=400,
                inclusive=True,
                status=Status.BORDERLINE,
                severity=Severity.ATTENTION,
                title="페리틴 경계 구간",
                summary=(
                    "페리틴이 {value} {unit}입니다. "
                    "150 ng/mL를 넘고 400 ng/mL 이하인 값은 남성 기준으로는 참고 구간 안일 수 있습니다. "
                    "성별이 없어 경계로 두었습니다."
                ),
            ),
            _high(
                "페리틴이 {value} {unit}입니다. "
                "400 ng/mL를 넘는 값은 성별과 관계없이 이 부품의 높은 구간입니다."
            ),
        ),
    }
