"""패널, 결과, 해석을 주고받는 공용 자료형.

분석 부품은 이 자료형만 알고, 다른 부품의 구현은 모릅니다.
"""

from __future__ import annotations

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any


class Sex(StrEnum):
    FEMALE = "female"
    MALE = "male"
    UNKNOWN = "unknown"


class Status(StrEnum):
    """참고 구간과 대조한 위치. 부품끼리 이 단어로 신호를 주고받습니다."""

    LOW = "low"
    BORDERLINE = "borderline"
    NORMAL = "normal"
    HIGH = "high"
    UNKNOWN = "unknown"


class Severity(StrEnum):
    INFO = "info"
    ATTENTION = "attention"
    URGENT = "urgent"


@dataclass(frozen=True)
class Subject:
    sex: Sex = Sex.UNKNOWN
    age_years: float | None = None

    def __post_init__(self) -> None:
        sex = self.sex if isinstance(self.sex, Sex) else Sex(str(self.sex))
        object.__setattr__(self, "sex", sex)
        if self.age_years is None:
            return
        age = float(self.age_years)
        if not math.isfinite(age) or age < 0 or age > 130:
            raise ValueError("나이 값이 올바르지 않습니다.")
        object.__setattr__(self, "age_years", age)


def adult_range_note(subject: Subject) -> str:
    if subject.age_years is not None and subject.age_years < 18:
        return " 이 부품의 구간은 성인 기준이라 미성년 결과에는 그대로 적용하기 어렵습니다."
    return ""


@dataclass(frozen=True)
class Result:
    code: str
    value: float
    unit: str = ""
    name: str = ""

    def __post_init__(self) -> None:
        code = self.code.strip()
        if not code:
            raise ValueError("검사 코드가 비어 있습니다.")
        value = float(self.value)
        if not math.isfinite(value):
            raise ValueError(f"검사 값이 숫자가 아닙니다: {code}")
        object.__setattr__(self, "code", code)
        object.__setattr__(self, "value", value)
        object.__setattr__(self, "unit", self.unit.strip())
        object.__setattr__(self, "name", self.name.strip())


@dataclass(frozen=True)
class Panel:
    results: tuple[Result, ...]
    subject: Subject = field(default_factory=Subject)

    def __post_init__(self) -> None:
        object.__setattr__(self, "results", tuple(self.results))
        if not isinstance(self.subject, Subject):
            raise TypeError("subject는 Subject여야 합니다.")


@dataclass(frozen=True)
class Finding:
    analyzer_id: str
    status: Status
    severity: Severity
    title: str
    summary: str
    codes: tuple[str, ...] = ()
    evidence: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        status = self.status if isinstance(self.status, Status) else Status(self.status)
        severity = (
            self.severity if isinstance(self.severity, Severity) else Severity(self.severity)
        )
        object.__setattr__(self, "status", status)
        object.__setattr__(self, "severity", severity)
        object.__setattr__(self, "codes", tuple(self.codes))
        object.__setattr__(self, "evidence", dict(self.evidence))


@dataclass(frozen=True)
class Report:
    findings: tuple[Finding, ...]
    unhandled: tuple[Result, ...] = ()
    subject: Subject = field(default_factory=Subject)

    def __post_init__(self) -> None:
        object.__setattr__(self, "findings", tuple(self.findings))
        object.__setattr__(self, "unhandled", tuple(self.unhandled))

    def to_dict(self) -> dict[str, Any]:
        from examkit.render import report_to_dict

        return report_to_dict(self)

    def to_text(self) -> str:
        from examkit.render import render_report

        return render_report(self)
