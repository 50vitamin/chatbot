"""비타민 B12 한 항목."""

from __future__ import annotations

from typing import ClassVar

from examkit.models import Severity, Status
from examkit.ranges import Band, RangeAnalyzer

_PMOL_TO_PG = 1 / 0.7378


class VitaminB12Analyzer(RangeAnalyzer):
    id = "vitamin_b12"
    description = "비타민 B12 한 항목을 성인 참고 구간과 대조합니다."
    codes = ("B12", "VITB12", "VITAMIN_B12")
    names = ("비타민B12", "비타민 B12", "vitamin B12", "cobalamin")
    expected_unit = "pg/mL"
    conversions: ClassVar[dict[str, float]] = {"pmol/L": _PMOL_TO_PG}
    bands = (
        Band(
            upper=200,
            inclusive=False,
            status=Status.LOW,
            severity=Severity.ATTENTION,
            title="비타민 B12가 낮은 구간",
            summary=(
                "비타민 B12가 {value} {unit}입니다. "
                "200 pg/mL 미만은 낮은 구간으로 보는 기준이 많습니다."
            ),
        ),
        Band(
            upper=300,
            inclusive=False,
            status=Status.BORDERLINE,
            severity=Severity.ATTENTION,
            title="비타민 B12 경계 구간",
            summary=(
                "비타민 B12가 {value} {unit}입니다. "
                "200 이상 300 pg/mL 미만은 경계 구간으로 두는 기준이 많습니다."
            ),
        ),
        Band(
            upper=900,
            inclusive=True,
            status=Status.NORMAL,
            severity=Severity.INFO,
            title="비타민 B12 참고 구간 안",
            summary="비타민 B12가 {value} {unit}로, 300–900 pg/mL 참고 구간 안에 있습니다.",
        ),
        Band(
            upper=None,
            inclusive=False,
            status=Status.HIGH,
            severity=Severity.INFO,
            title="비타민 B12가 높은 구간",
            summary=(
                "비타민 B12가 {value} {unit}입니다. "
                "900 pg/mL를 넘는 값은 높은 구간으로 분류됩니다."
            ),
        ),
    )
