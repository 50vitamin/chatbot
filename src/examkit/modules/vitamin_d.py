"""25-OH 비타민 D 한 항목."""

from __future__ import annotations

from typing import ClassVar

from examkit.models import Severity, Status
from examkit.ranges import Band, RangeAnalyzer

_NMOL_TO_NG = 1 / 2.496


class VitaminDAnalyzer(RangeAnalyzer):
    id = "vitamin_d"
    description = "25-OH 비타민 D 한 항목을 성인 참고 구간과 대조합니다."
    codes = ("25OHD", "25-OH-D", "VITD", "VITAMIN_D")
    names = ("비타민D", "비타민 D", "vitamin D", "25-hydroxyvitamin D")
    expected_unit = "ng/mL"
    conversions: ClassVar[dict[str, float]] = {"nmol/L": _NMOL_TO_NG}
    bands = (
        Band(
            upper=12,
            inclusive=False,
            status=Status.LOW,
            severity=Severity.URGENT,
            title="비타민 D가 매우 낮은 구간",
            summary=(
                "25-OH 비타민 D가 {value} {unit}입니다. "
                "흔히 인용되는 기준에서 12 ng/mL 미만은 심한 결핍 구간으로 봅니다."
            ),
        ),
        Band(
            upper=20,
            inclusive=False,
            status=Status.LOW,
            severity=Severity.ATTENTION,
            title="비타민 D 결핍 구간",
            summary=(
                "25-OH 비타민 D가 {value} {unit}입니다. "
                "흔히 인용되는 기준에서 20 ng/mL 미만은 결핍 구간입니다."
            ),
        ),
        Band(
            upper=30,
            inclusive=False,
            status=Status.BORDERLINE,
            severity=Severity.ATTENTION,
            title="비타민 D 불충분 구간",
            summary=(
                "25-OH 비타민 D가 {value} {unit}입니다. "
                "20 이상 30 ng/mL 미만은 불충분 구간으로 보는 기준이 많습니다."
            ),
        ),
        Band(
            upper=100,
            inclusive=True,
            status=Status.NORMAL,
            severity=Severity.INFO,
            title="비타민 D 참고 구간 안",
            summary="25-OH 비타민 D가 {value} {unit}로, 30–100 ng/mL 참고 구간 안에 있습니다.",
        ),
        Band(
            upper=None,
            inclusive=False,
            status=Status.HIGH,
            severity=Severity.ATTENTION,
            title="비타민 D가 높은 구간",
            summary=(
                "25-OH 비타민 D가 {value} {unit}입니다. "
                "100 ng/mL를 넘는 값은 높은 구간으로 분류하는 기준이 많습니다."
            ),
        ),
    )
