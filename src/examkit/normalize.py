"""코드, 이름, 단위를 같은 꼴로 맞춥니다."""

from __future__ import annotations


def normalize_code(value: str) -> str:
    """공백과 기호를 빼고 비교용 키를 만듭니다."""

    return "".join(ch for ch in value.casefold() if ch.isalnum())


def normalize_unit(value: str) -> str:
    return (
        value.strip()
        .replace("µ", "u")
        .replace("μ", "u")
        .replace(" ", "")
        .casefold()
    )


def format_number(value: float) -> str:
    rounded = round(float(value), 2)
    text = f"{rounded:.2f}"
    if text.endswith("00"):
        return str(int(rounded))
    if text.endswith("0"):
        return text[:-1]
    return text
