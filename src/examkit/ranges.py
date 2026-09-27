"""숫자 하나를 참고 구간과 대조하는 결과 부품용 뼈대."""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar

from examkit.analyzer import Analyzer
from examkit.models import (
    Finding,
    Result,
    Severity,
    Sex,
    Status,
    Subject,
    adult_range_note,
    sheet_note,
)
from examkit.normalize import format_number, normalize_unit


@dataclass(frozen=True)
class Band:
    """앞에서부터 첫 번째로 맞는 구간을 씁니다. 낮은 값부터 나열하세요."""

    upper: float | None
    inclusive: bool
    status: Status
    severity: Severity
    title: str
    summary: str

    def matches(self, value: float) -> bool:
        if self.upper is None:
            return True
        if self.inclusive:
            return value <= self.upper
        return value < self.upper


@dataclass(frozen=True)
class Converted:
    value: float | None
    assumed: bool = False
    original_value: float | None = None
    original_unit: str = ""
    factor: float | None = None
    error: str = ""

    def note(self, expected_unit: str) -> str:
        if self.error or self.value is None:
            return ""
        if self.assumed:
            return f" 단위가 비어 있어 {expected_unit}로 해석했습니다."
        if self.original_unit and normalize_unit(self.original_unit) != normalize_unit(expected_unit):
            if self.factor == 1:
                return (
                    f" 입력 단위 {self.original_unit}는 {expected_unit}와 같은 척도로 읽었습니다."
                )
            return (
                f" 입력값 {format_number(self.original_value or 0)} {self.original_unit}를 "
                f"{expected_unit}로 환산했습니다."
            )
        return ""


class RangeAnalyzer(Analyzer):
    """단위를 맞춘 뒤 ``bands`` 또는 ``bands_by_sex``로 상태를 정합니다."""

    abstract: ClassVar[bool] = True
    expected_unit: ClassVar[str] = ""
    conversions: ClassVar[dict[str, float]] = {}
    bands: ClassVar[tuple[Band, ...]] = ()
    bands_by_sex: ClassVar[dict[Sex, tuple[Band, ...]]] = {}

    def bands_for(self, subject: Subject) -> tuple[Band, ...]:
        if not self.bands_by_sex:
            return self.bands
        specific = self.bands_by_sex.get(subject.sex)
        if specific:
            return specific
        return self.bands_by_sex.get(Sex.UNKNOWN, self.bands)

    def analyze_result(self, result: Result, subject: Subject) -> list[Finding]:
        converted = convert_value(result, self.expected_unit, self.conversions)
        if converted.error or converted.value is None:
            return [self._unit_error(result, converted.error or "값을 읽지 못했습니다.")]
        band = next(
            (item for item in self.bands_for(subject) if item.matches(converted.value)),
            None,
        )
        if band is None:
            return [self._missing_band(result, converted.value)]
        shown = format_number(converted.value)
        summary = band.summary.format(value=shown, unit=self.expected_unit)
        summary += converted.note(self.expected_unit)
        summary += adult_range_note(subject)
        summary += sheet_note(result)
        return [
            Finding(
                analyzer_id=self.id,
                status=band.status,
                severity=band.severity,
                title=band.title,
                summary=summary,
                codes=(result.code,),
                evidence={
                    "input_code": result.code,
                    "input_value": result.value,
                    "input_unit": result.unit,
                    "value": converted.value,
                    "unit": self.expected_unit,
                    "assumed_unit": converted.assumed,
                    "canonical_code": self.codes[0] if self.codes else result.code,
                },
            )
        ]

    def _unit_error(self, result: Result, reason: str) -> Finding:
        label = result.name or result.code
        return Finding(
            analyzer_id=self.id,
            status=Status.UNKNOWN,
            severity=Severity.ATTENTION,
            title="단위를 해석할 수 없음",
            summary=(
                f"{label} 값 {format_number(result.value)}의 단위 "
                f"'{result.unit}'는 이 부품이 아는 단위가 아닙니다. {reason}"
            ),
            codes=(result.code,),
            evidence={"input_code": result.code, "input_unit": result.unit},
        )

    def _missing_band(self, result: Result, value: float) -> Finding:
        label = result.name or result.code
        return Finding(
            analyzer_id=self.id,
            status=Status.UNKNOWN,
            severity=Severity.ATTENTION,
            title="구간을 정하지 못함",
            summary=(
                f"{label} 값 {format_number(value)} {self.expected_unit}에 "
                "해당하는 구간이 이 부품에 없습니다."
            ),
            codes=(result.code,),
            evidence={"input_code": result.code, "value": value, "unit": self.expected_unit},
        )


def convert_value(
    result: Result,
    expected_unit: str,
    conversions: dict[str, float],
) -> Converted:
    if not result.unit:
        return Converted(
            value=result.value,
            assumed=True,
            original_value=result.value,
            original_unit="",
        )
    incoming = normalize_unit(result.unit)
    if incoming == normalize_unit(expected_unit):
        return Converted(value=result.value, original_value=result.value, original_unit=result.unit)
    factor = _conversion_factor(incoming, conversions)
    if factor is None:
        expected = expected_unit or "지정된 단위"
        return Converted(
            value=None,
            original_value=result.value,
            original_unit=result.unit,
            error=f"기대 단위는 {expected}입니다.",
        )
    return Converted(
        value=result.value * factor,
        original_value=result.value,
        original_unit=result.unit,
        factor=factor,
    )


def _conversion_factor(incoming: str, conversions: dict[str, float]) -> float | None:
    for unit, factor in conversions.items():
        if normalize_unit(unit) == incoming:
            return factor
    return None
