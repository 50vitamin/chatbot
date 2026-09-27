import json
from pathlib import Path

import pytest

from examkit.analyzer import Analyzer
from examkit.models import Sex
from examkit.parse import ParseError, load_panel, loads_panel, resolve_label
from examkit.pipeline import Pipeline
from examkit.registry import Registry

ROOT = Path(__file__).parents[1]


def test_text_and_json_sample_hit_the_same_parts():
    registry = Registry.discover()
    from_json = load_panel(str(ROOT / "examples" / "sample_panel.json"), registry)
    from_text = load_panel(str(ROOT / "examples" / "sample_panel.txt"), registry)
    json_report = Pipeline(registry).run(from_json)
    text_report = Pipeline(registry).run(from_text)
    assert from_json.subject.sex is Sex.FEMALE
    assert from_json.subject.age_years == 34
    assert [result.code for result in from_text.results] == [
        "25OHD",
        "B12",
        "FERRITIN",
        "HGB",
        "CRP",
    ]
    assert [finding.analyzer_id for finding in json_report.findings] == [
        finding.analyzer_id for finding in text_report.findings
    ]
    assert [finding.title for finding in json_report.findings] == [
        finding.title for finding in text_report.findings
    ]


def test_korean_json_sex_numbers_and_bad_lines():
    panel = loads_panel(
        json.dumps(
            {
                "subject": {"sex": "여성", "age_years": 34},
                "results": [{"code": "HB", "value": 11, "unit": "g/dL"}],
            }
        )
    )
    assert panel.subject.sex is Sex.FEMALE
    report = Pipeline.discover().run(panel)
    assert report.findings[0].analyzer_id == "hemoglobin"

    text = loads_panel("비타민 D 18,5 ng/mL\nCRP 1,200 mg/L\n")
    assert text.results[0].value == 18.5
    assert text.results[1].value == 1200

    with pytest.raises(ParseError, match="2번째 줄"):
        loads_panel("# 메모\n그냥 문장\n")
    with pytest.raises(ParseError, match="나이"):
        loads_panel("나이 서른넷\n")
    with pytest.raises(ParseError, match="JSON"):
        loads_panel("{")


def test_shared_name_must_point_at_one_code():
    class Alpha(Analyzer):
        id = "alpha"
        codes = ("AAA",)
        names = ("같은이름",)

    class Beta(Analyzer):
        id = "beta"
        codes = ("BBB",)
        names = ("같은이름",)

    registry = Registry()
    registry.register(Alpha())
    registry.register(Beta())
    with pytest.raises(ParseError, match="alpha, beta"):
        resolve_label("같은이름", registry)
