from examkit.models import Panel, Result, Sex, Status, Subject
from examkit.parse import loads_panel
from examkit.pipeline import Pipeline
from examkit.registry import Registry


def _run(results, sex=Sex.FEMALE):
    return Pipeline.discover().run(Panel(results=tuple(results), subject=Subject(sex=sex)))


def test_sheet_reference_covers_a_blood_row_with_no_dedicated_part():
    report = _run((Result("GLU", 92, "mg/dL", "공복혈당", reference_low=70, reference_high=99),))
    finding = report.findings[0]
    assert finding.analyzer_id == "printed_reference"
    assert finding.status is Status.NORMAL
    assert finding.title == "결과지 참고치 안: 공복혈당"
    assert report.unhandled == ()


def test_dedicated_part_keeps_the_row_and_still_mentions_the_sheet():
    report = _run(
        (Result("HGB", 10.8, "g/dL", "헤모글로빈", reference_low=12, reference_high=15.5),)
    )
    assert [finding.analyzer_id for finding in report.findings] == ["hemoglobin"]
    assert "결과지 참고치는 12–15.5 g/dL입니다." in report.findings[0].summary

    registry = Registry.discover()
    registry.disable("hemoglobin")
    fallback = Pipeline(registry).run(
        Panel(
            results=(Result("HGB", 10.8, "g/dL", "헤모글로빈", reference_low=12, reference_high=15.5),),
            subject=Subject(sex=Sex.FEMALE),
        )
    )
    assert fallback.findings[0].analyzer_id == "printed_reference"
    assert fallback.findings[0].status is Status.LOW
    assert "anemia_pattern" not in {finding.analyzer_id for finding in fallback.findings}


def test_open_reference_and_flag_only_rows():
    high = _run((Result("CRP", 0.5, "mg/dL", "CRP", reference_high=0.5, reference_high_inclusive=False),))
    assert high.findings[0].status is Status.HIGH

    inside = _run((Result("CRP", 0.4, "mg/dL", "CRP", reference_high=0.5, reference_high_inclusive=False),))
    assert inside.findings[0].status is Status.NORMAL

    flagged = _run((Result("ESR", 30, "mm/h", "ESR", flag="H"),))
    assert flagged.findings[0].title == "결과지에 높음으로 표시: ESR"


def test_text_sheet_parses_reference_intervals():
    panel = loads_panel("공복혈당 92 mg/dL 참고 70~99\nCRP 0.8 mg/dL 참고 <0.5\nESR 22 mm/h H\n")
    glucose, crp, esr = panel.results
    assert (glucose.reference_low, glucose.reference_high) == (70, 99)
    assert crp.reference_low is None
    assert crp.reference_high == 0.5
    assert crp.reference_high_inclusive is False
    assert esr.flag == "H"
    assert esr.has_reference is False
