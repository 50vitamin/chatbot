"""기본 꾸러미 밖에 두는 부품 예시.

examkit 패키지 안이 아니므로 자동으로 붙지 않습니다.
Registry.register 또는 진입점 examkit.analyzers 로 끼웁니다.
"""

from examkit.models import Severity, Status
from examkit.ranges import Band, RangeAnalyzer


class TshAnalyzer(RangeAnalyzer):
    id = "tsh"
    description = "TSH 예시 부품. 원할 때 직접 등록합니다."
    codes = ("TSH",)
    names = ("TSH", "갑상선자극호르몬")
    expected_unit = "uIU/mL"
    conversions = {"mIU/L": 1.0}
    bands = (
        Band(
            upper=0.4,
            inclusive=False,
            status=Status.LOW,
            severity=Severity.ATTENTION,
            title="TSH가 낮은 구간",
            summary=(
                "TSH가 {value} {unit}입니다. "
                "성인에서 흔히 0.4 uIU/mL 미만을 낮은 구간으로 봅니다."
            ),
        ),
        Band(
            upper=4.5,
            inclusive=True,
            status=Status.NORMAL,
            severity=Severity.INFO,
            title="TSH 참고 구간 안",
            summary="TSH가 {value} {unit}로, 0.4–4.5 uIU/mL 참고 구간 안에 있습니다.",
        ),
        Band(
            upper=None,
            inclusive=False,
            status=Status.HIGH,
            severity=Severity.ATTENTION,
            title="TSH가 높은 구간",
            summary=(
                "TSH가 {value} {unit}입니다. "
                "4.5 uIU/mL를 넘는 값은 높은 구간으로 자주 분류됩니다."
            ),
        ),
    )
