"""사람이 적은 문장이나 JSON을 패널로 바꿉니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from examkit.models import Panel, Result, Sex, Subject
from examkit.normalize import normalize_code
from examkit.registry import Registry

_SEX = {
    "여": Sex.FEMALE,
    "여성": Sex.FEMALE,
    "여자": Sex.FEMALE,
    "f": Sex.FEMALE,
    "female": Sex.FEMALE,
    "남": Sex.MALE,
    "남성": Sex.MALE,
    "남자": Sex.MALE,
    "m": Sex.MALE,
    "male": Sex.MALE,
    "미상": Sex.UNKNOWN,
    "unknown": Sex.UNKNOWN,
}

_SEX_KEYS = {"성별", "sex"}
_AGE_KEYS = {"나이", "age", "age_years"}


class ParseError(ValueError):
    """패널 문서를 읽지 못할 때."""


def load_panel(path: str, registry: Registry | None = None) -> Panel:
    text = Path(path).read_text(encoding="utf-8")
    return loads_panel(text, registry)


def loads_panel(text: str, registry: Registry | None = None) -> Panel:
    stripped = text.lstrip("\ufeff").lstrip()
    if stripped.startswith("{") or stripped.startswith("["):
        try:
            data = json.loads(stripped)
        except json.JSONDecodeError as exc:
            raise ParseError(f"JSON을 읽지 못했습니다: {exc.msg}") from exc
        return panel_from_data(data)
    return parse_panel(text, registry)


def panel_from_data(data: Any) -> Panel:
    if not isinstance(data, dict):
        raise ParseError("패널 JSON은 객체여야 합니다.")
    subject_data = data.get("subject") or {}
    if not isinstance(subject_data, dict):
        raise ParseError("subject는 객체여야 합니다.")
    raw_results = data.get("results") or []
    if not isinstance(raw_results, list):
        raise ParseError("results는 배열이어야 합니다.")
    results: list[Result] = []
    for index, item in enumerate(raw_results, start=1):
        if not isinstance(item, dict) or "code" not in item or "value" not in item:
            raise ParseError(f"{index}번째 결과에 code와 value가 필요합니다.")
        try:
            results.append(
                Result(
                    code=str(item["code"]),
                    value=float(item["value"]),
                    unit=str(item.get("unit") or ""),
                    name=str(item.get("name") or ""),
                )
            )
        except (TypeError, ValueError) as exc:
            raise ParseError(f"{index}번째 결과를 읽지 못했습니다: {exc}") from exc
    try:
        subject = Subject(
            sex=_sex_value(subject_data.get("sex", Sex.UNKNOWN)),
            age_years=subject_data.get("age_years"),
        )
    except (TypeError, ValueError) as exc:
        raise ParseError(f"대상 정보를 읽지 못했습니다: {exc}") from exc
    return Panel(results=tuple(results), subject=subject)


def parse_panel(text: str, registry: Registry | None = None) -> Panel:
    active = registry if registry is not None else Registry.discover()
    sex = Sex.UNKNOWN
    age: float | None = None
    results: list[Result] = []
    for line_number, raw in enumerate(text.splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        meta = _meta_pair(line)
        if meta is not None:
            key, value = meta
            if key in _SEX_KEYS:
                sex = _parse_sex(value, line_number)
                continue
            if key in _AGE_KEYS:
                age = _parse_age(value, line_number)
                continue
        try:
            results.append(_parse_measurement(line, active))
        except ParseError as exc:
            raise ParseError(f"{line_number}번째 줄: {exc}") from exc
    return Panel(results=tuple(results), subject=Subject(sex=sex, age_years=age))


def resolve_label(label: str, registry: Registry) -> str:
    """이름이나 별칭을 부품의 대표 코드로 바꿉니다. 모르면 입력 그대로 둡니다."""

    key = normalize_code(label)
    if not key:
        raise ParseError("검사 이름이 비어 있습니다.")
    owners: list[tuple[str, str]] = []
    for analyzer in registry:
        if not analyzer.codes:
            continue
        claimed = any(normalize_code(code) == key for code in analyzer.codes)
        if not claimed:
            claimed = any(normalize_code(name) == key for name in analyzer.names)
        if claimed:
            owners.append((analyzer.id, analyzer.codes[0]))
    if not owners:
        return label.strip()
    canonicals = {normalize_code(code) for _, code in owners}
    if len(canonicals) > 1:
        names = ", ".join(sorted(part_id for part_id, _ in owners))
        raise ParseError(
            f"'{label}' 이름을 여러 부품이 서로 다른 코드로 씁니다: {names}. 검사 코드를 직접 적어 주세요."
        )
    return owners[0][1]


def _meta_pair(line: str) -> tuple[str, str] | None:
    for separator in (":", "="):
        if separator in line:
            key, value = line.split(separator, 1)
            key = key.strip().casefold()
            if key in _SEX_KEYS or key in _AGE_KEYS:
                return key, value.strip()
            return None
    parts = line.split()
    if len(parts) >= 2 and parts[0].casefold() in _SEX_KEYS | _AGE_KEYS:
        return parts[0].casefold(), " ".join(parts[1:])
    return None


def _sex_value(value: object) -> Sex:
    if isinstance(value, Sex):
        return value
    text = str(value).strip()
    sex = _SEX.get(text.casefold())
    if sex is not None:
        return sex
    return Sex(text)


def _parse_sex(value: str, line_number: int) -> Sex:
    try:
        return _sex_value(value)
    except ValueError as exc:
        raise ParseError(f"{line_number}번째 줄: 성별을 읽지 못했습니다: {value}") from exc


def _parse_age(value: str, line_number: int) -> float:
    cleaned = value.replace("세", "").strip()
    try:
        return _parse_number(cleaned)
    except ValueError as exc:
        raise ParseError(f"{line_number}번째 줄: 나이를 숫자로 읽지 못했습니다: {value}") from exc


def _parse_measurement(line: str, registry: Registry) -> Result:
    tokens = line.split()
    for index, token in enumerate(tokens):
        try:
            value = _parse_number(token)
        except ValueError:
            continue
        if index == 0:
            break
        label = " ".join(tokens[:index])
        unit = " ".join(tokens[index + 1 :])
        code = resolve_label(label, registry)
        return Result(code=code, value=value, unit=unit, name=label)
    raise ParseError(f"검사 값 형식이 아닙니다: {line}")


def _parse_number(token: str) -> float:
    text = token.strip()
    if not text:
        raise ValueError
    if "," in text and "." not in text:
        left, right = text.split(",", 1)
        if right.isdigit() and len(right) != 3:
            text = f"{left}.{right}"
        else:
            text = text.replace(",", "")
    else:
        text = text.replace(",", "")
    return float(text)
