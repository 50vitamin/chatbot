"""사람이 적은 문장이나 JSON을 패널로 바꿉니다."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from examkit.models import Panel, Result, Sex, Subject, normalize_flag
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
            results.append(_result_from_mapping(item))
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


_REF_WORDS = {"참고", "참고치", "ref", "reference"}


def _result_from_mapping(item: dict[str, Any]) -> Result:
    low, high, low_inclusive, high_inclusive = _reference_fields(item)
    return Result(
        code=str(item["code"]),
        value=float(item["value"]),
        unit=str(item.get("unit") or ""),
        name=str(item.get("name") or ""),
        reference_low=low,
        reference_high=high,
        reference_low_inclusive=low_inclusive,
        reference_high_inclusive=high_inclusive,
        flag=str(item.get("flag") or ""),
    )


def _reference_fields(item: dict[str, Any]) -> tuple[float | None, float | None, bool, bool]:
    has_bounds = "reference_low" in item or "reference_high" in item
    if has_bounds:
        return (
            _optional_float(item.get("reference_low")),
            _optional_float(item.get("reference_high")),
            bool(item.get("reference_low_inclusive", True)),
            bool(item.get("reference_high_inclusive", True)),
        )
    if item.get("reference"):
        return _parse_interval(str(item["reference"]))
    return None, None, True, True


def _optional_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    return float(value)


def _parse_measurement(line: str, registry: Registry) -> Result:
    tokens = line.split()
    value_index: int | None = None
    value: float | None = None
    for index, token in enumerate(tokens):
        try:
            parsed = _parse_number(token)
        except ValueError:
            continue
        if index == 0:
            break
        value_index = index
        value = parsed
        break
    if value_index is None or value is None:
        raise ParseError(f"혈액검사 값 형식이 아닙니다: {line}")
    label = " ".join(tokens[:value_index])
    unit_tokens, interval, flag = _split_tail(tokens[value_index + 1 :])
    low = high = None
    low_inclusive = high_inclusive = True
    if interval is not None:
        low, high, low_inclusive, high_inclusive = _parse_interval(interval)
    code = resolve_label(label, registry)
    return Result(
        code=code,
        value=value,
        unit=" ".join(unit_tokens),
        name=label,
        reference_low=low,
        reference_high=high,
        reference_low_inclusive=low_inclusive,
        reference_high_inclusive=high_inclusive,
        flag=flag,
    )


def _split_tail(tokens: list[str]) -> tuple[list[str], str | None, str]:
    ref_at = next((index for index, token in enumerate(tokens) if _is_reference_word(token)), None)
    if ref_at is None:
        if tokens and _flag_or_empty(tokens[-1]):
            return tokens[:-1], None, normalize_flag(tokens[-1])
        return tokens, None, ""
    ref_token = tokens[ref_at]
    if ":" in ref_token and ref_token.split(":", 1)[1].strip():
        ref_bits = [ref_token.split(":", 1)[1].strip(), *tokens[ref_at + 1 :]]
    else:
        ref_bits = tokens[ref_at + 1 :]
    flag = ""
    if ref_bits and _flag_or_empty(ref_bits[-1]):
        flag = normalize_flag(ref_bits[-1])
        ref_bits = ref_bits[:-1]
    if not ref_bits:
        raise ParseError("참고치 구간이 없습니다.")
    return tokens[:ref_at], " ".join(ref_bits), flag


def _is_reference_word(token: str) -> bool:
    head = token.split(":", 1)[0].strip().casefold()
    return head in _REF_WORDS


def _flag_or_empty(token: str) -> bool:
    try:
        return normalize_flag(token) != ""
    except ValueError:
        return False


def _parse_interval(text: str) -> tuple[float | None, float | None, bool, bool]:
    raw = text.strip().replace(" ", "").replace("~", "-").replace("～", "-").replace("–", "-").replace("—", "-")
    if not raw:
        raise ParseError("참고치 구간이 없습니다.")
    try:
        if raw.startswith("<="):
            return None, _parse_number(raw[2:]), True, True
        if raw.startswith("<"):
            return None, _parse_number(raw[1:]), True, False
        if raw.startswith(">="):
            return _parse_number(raw[2:]), None, True, True
        if raw.startswith(">"):
            return _parse_number(raw[1:]), None, False, True
        left, right = raw.split("-", 1)
        low = _parse_number(left)
        high = _parse_number(right)
    except ValueError as exc:
        raise ParseError(f"참고치를 읽지 못했습니다: {text}") from exc
    if low > high:
        raise ParseError(f"참고치의 하한이 상한보다 큽니다: {text}")
    return low, high, True, True


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
