"""분석 부품이 구현하는 소켓."""

from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar

from examkit.models import Finding, Panel, Result, Subject
from examkit.normalize import normalize_code


class Analyzer:
    """혈액검사 항목 하나, 또는 여러 항목의 패턴을 해석하는 부품.

    결과 부품은 ``codes``에 맡은 코드를 적고 ``analyze_result``를 구현합니다.
    ``fallback`` 부품은 다른 결과 부품이 맡지 않은 줄만 받습니다.
    패널 부품은 ``scope = "panel"``로 두고, 앞선 부품이 만든 ``Finding.status``를
    읽어 ``analyze_panel``에서 조합합니다. 생성자는 인자 없이 호출됩니다.
    """

    id: ClassVar[str] = ""
    description: ClassVar[str] = ""
    scope: ClassVar[str] = "result"
    codes: ClassVar[tuple[str, ...]] = ()
    names: ClassVar[tuple[str, ...]] = ()
    uses: ClassVar[tuple[str, ...]] = ()
    fallback: ClassVar[bool] = False
    abstract: ClassVar[bool] = False

    def matches(self, result: Result) -> bool:
        key = normalize_code(result.code)
        return any(normalize_code(code) == key for code in self.codes)

    def analyze_result(self, result: Result, subject: Subject) -> list[Finding]:
        return []

    def analyze_panel(self, panel: Panel, findings: Sequence[Finding]) -> list[Finding]:
        return []
