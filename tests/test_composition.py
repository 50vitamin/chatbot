from examkit.analyzer import Analyzer
from examkit.models import Finding, Panel, Result, Severity, Sex, Status, Subject
from examkit.pipeline import Pipeline
from examkit.registry import Registry


def _panel(results, sex=Sex.FEMALE, age=34):
    return Panel(results=tuple(results), subject=Subject(sex=sex, age_years=age))


def _sample_results():
    return (
        Result("25OHD", 18, "ng/mL", "비타민 D"),
        Result("B12", 180, "pg/mL", "비타민 B12"),
        Result("FERRITIN", 12, "ng/mL", "페리틴"),
        Result("HGB", 10.8, "g/dL", "헤모글로빈"),
        Result("CRP", 1.2, "mg/L", "CRP"),
    )


def test_sample_panel_snaps_single_parts_and_the_pattern_part_together():
    report = Pipeline.discover().run(_panel(_sample_results()))
    assert [finding.analyzer_id for finding in report.findings] == [
        "vitamin_d",
        "vitamin_b12",
        "ferritin",
        "hemoglobin",
        "anemia_pattern",
    ]
    pattern = report.findings[-1]
    assert pattern.title == "헤모글로빈, 페리틴, 비타민 B12가 함께 낮은 패턴"
    assert pattern.evidence["based_on"] == ["hemoglobin", "ferritin", "vitamin_b12"]
    assert pattern.codes == ("B12", "FERRITIN", "HGB")
    assert [result.code for result in report.unhandled] == ["CRP"]
    assert "진단, 치료, 복용 결정" in report.to_text()


def test_pattern_part_speaks_only_from_other_parts_status():
    registry = Registry.discover()
    registry.disable("ferritin")
    report = Pipeline(registry).run(_panel(_sample_results()))
    assert "ferritin" not in {finding.analyzer_id for finding in report.findings}
    assert report.findings[-1].title == "헤모글로빈과 비타민 B12가 함께 낮은 패턴"
    assert "FERRITIN" in {result.code for result in report.unhandled}

    iron_only = Pipeline.discover().run(
        _panel(
            (
                Result("FERRITIN", 12, "ng/mL"),
                Result("HGB", 10.8, "g/dL"),
                Result("B12", 500, "pg/mL"),
            )
        )
    )
    assert iron_only.findings[-1].title == "헤모글로빈과 페리틴이 함께 낮은 패턴"

    no_pattern = Pipeline.discover().run(
        _panel((Result("FERRITIN", 40, "ng/mL"), Result("HGB", 10.8, "g/dL")))
    )
    assert "anemia_pattern" not in {finding.analyzer_id for finding in no_pattern.findings}


def test_replacement_part_with_the_same_id_still_feeds_the_pattern():
    class WiderFerritin(Analyzer):
        id = "ferritin"
        description = "더 엄격한 페리틴 부품"
        codes = ("FERRITIN",)

        def analyze_result(self, result, subject):
            status = Status.LOW if result.value < 50 else Status.NORMAL
            return [
                Finding(
                    analyzer_id=self.id,
                    status=status,
                    severity=Severity.ATTENTION,
                    title="교체된 페리틴 부품",
                    summary="교체 부품이 해석했습니다.",
                    codes=(result.code,),
                )
            ]

    registry = Registry.discover()
    registry.unregister("ferritin")
    registry.register(WiderFerritin())
    report = Pipeline(registry).run(
        _panel((Result("FERRITIN", 40, "ng/mL"), Result("HGB", 10.8, "g/dL")))
    )
    assert any(finding.title == "교체된 페리틴 부품" for finding in report.findings)
    assert report.findings[-1].evidence["based_on"] == ["hemoglobin", "ferritin"]


def test_one_broken_part_does_not_stop_the_others():
    class Boom(Analyzer):
        id = "boom"
        codes = ("HGB",)

        def analyze_result(self, result, subject):
            raise RuntimeError("깨짐")

    registry = Registry.discover()
    registry.register(Boom())
    report = Pipeline(registry).run(_panel((Result("HGB", 10.8, "g/dL"),)))
    by_id = {finding.analyzer_id: finding for finding in report.findings}
    assert by_id["hemoglobin"].status is Status.LOW
    assert by_id["boom"].title == "분석 부품 오류"
    assert by_id["boom"].evidence["error_type"] == "RuntimeError"
    assert "깨짐" in by_id["boom"].summary


def test_urgent_finding_is_shown_first_without_changing_machine_order():
    report = Pipeline.discover().run(
        _panel((Result("HGB", 7, "g/dL"), Result("25OHD", 40, "ng/mL")))
    )
    assert [finding.analyzer_id for finding in report.findings] == ["hemoglobin", "vitamin_d"]
    text = report.to_text()
    assert text.index("확인 필요") < text.index("참고")


def test_empty_panel():
    report = Pipeline.discover().run(_panel(()))
    assert report.findings == ()
    assert "해석할 검사 항목이 없습니다." in report.to_text()
