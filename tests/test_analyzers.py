from examkit.models import Panel, Result, Sex, Status, Subject
from examkit.modules.ferritin import FerritinAnalyzer
from examkit.modules.hemoglobin import HemoglobinAnalyzer
from examkit.modules.vitamin_b12 import VitaminB12Analyzer
from examkit.modules.vitamin_d import VitaminDAnalyzer
from examkit.pipeline import Pipeline
from examkit.registry import Registry


def _one(analyzer, value, unit, sex=Sex.FEMALE, age=34):
    registry = Registry()
    registry.register(analyzer)
    report = Pipeline(registry).run(
        Panel(
            results=(Result(code=analyzer.codes[0], value=value, unit=unit),),
            subject=Subject(sex=sex, age_years=age),
        )
    )
    assert len(report.findings) == 1
    return report.findings[0]


def test_vitamin_d_bands_and_unit_conversion():
    assert _one(VitaminDAnalyzer(), 10, "ng/mL").severity.value == "urgent"
    assert _one(VitaminDAnalyzer(), 18, "ng/mL").status is Status.LOW
    assert _one(VitaminDAnalyzer(), 20, "ng/mL").status is Status.BORDERLINE
    assert _one(VitaminDAnalyzer(), 30, "ng/mL").status is Status.NORMAL
    assert _one(VitaminDAnalyzer(), 100, "ng/mL").status is Status.NORMAL
    assert _one(VitaminDAnalyzer(), 100.01, "ng/mL").status is Status.HIGH

    converted = _one(VitaminDAnalyzer(), 60, "nmol/L")
    assert converted.status is Status.BORDERLINE
    assert "24.04 ng/mL" in converted.summary
    assert "nmol/L" in converted.summary

    unknown = _one(VitaminDAnalyzer(), 18, "mg/dL")
    assert unknown.status is Status.UNKNOWN
    assert unknown.title == "단위를 해석할 수 없음"

    assumed = _one(VitaminDAnalyzer(), 18, "")
    assert assumed.status is Status.LOW
    assert "단위가 비어 있어" in assumed.summary


def test_minor_age_is_called_out():
    finding = _one(VitaminDAnalyzer(), 40, "ng/mL", age=10)
    assert finding.status is Status.NORMAL
    assert finding.summary.endswith("미성년 결과에는 그대로 적용하기 어렵습니다.")


def test_b12_boundaries():
    assert _one(VitaminB12Analyzer(), 199, "pg/mL").status is Status.LOW
    assert _one(VitaminB12Analyzer(), 200, "pg/mL").status is Status.BORDERLINE
    assert _one(VitaminB12Analyzer(), 300, "pg/mL").status is Status.NORMAL
    assert _one(VitaminB12Analyzer(), 900, "pg/mL").status is Status.NORMAL
    low = _one(VitaminB12Analyzer(), 100, "pmol/L")
    assert low.status is Status.LOW
    assert "환산" in low.summary


def test_ferritin_depends_on_sex():
    assert _one(FerritinAnalyzer(), 20, "ng/mL", Sex.FEMALE).status is Status.NORMAL
    assert _one(FerritinAnalyzer(), 20, "ng/mL", Sex.MALE).status is Status.LOW
    assert _one(FerritinAnalyzer(), 200, "ng/mL", Sex.FEMALE).status is Status.HIGH
    assert _one(FerritinAnalyzer(), 200, "ng/mL", Sex.MALE).status is Status.NORMAL
    assert _one(FerritinAnalyzer(), 20, "ng/mL", Sex.UNKNOWN).status is Status.BORDERLINE
    assert _one(FerritinAnalyzer(), 500, "ug/L", Sex.MALE).status is Status.HIGH
    same_scale = _one(FerritinAnalyzer(), 80, "µg/L", Sex.FEMALE)
    assert same_scale.status is Status.NORMAL
    assert "같은 척도" in same_scale.summary


def test_hemoglobin_depends_on_sex_and_flags_very_low_values():
    assert _one(HemoglobinAnalyzer(), 7.2, "g/dL").severity.value == "urgent"
    assert _one(HemoglobinAnalyzer(), 11.5, "g/dL", Sex.FEMALE).status is Status.LOW
    assert _one(HemoglobinAnalyzer(), 12.5, "g/dL", Sex.FEMALE).status is Status.NORMAL
    assert _one(HemoglobinAnalyzer(), 12.5, "g/dL", Sex.MALE).status is Status.LOW
    assert _one(HemoglobinAnalyzer(), 14, "g/dL", Sex.MALE).status is Status.NORMAL
    assert _one(HemoglobinAnalyzer(), 12.5, "g/dL", Sex.UNKNOWN).status is Status.BORDERLINE
    assert _one(HemoglobinAnalyzer(), 16, "g/dL", Sex.UNKNOWN).status is Status.BORDERLINE
    assert _one(HemoglobinAnalyzer(), 18, "g/dL", Sex.UNKNOWN).status is Status.HIGH
    from_grams = _one(HemoglobinAnalyzer(), 108, "g/L", Sex.FEMALE)
    assert from_grams.status is Status.LOW
    assert "10.8 g/dL" in from_grams.summary
    assert _one(HemoglobinAnalyzer(), 12, "g/dL", Sex.FEMALE).status is Status.NORMAL
