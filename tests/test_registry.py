import importlib.util
from pathlib import Path
from types import ModuleType

import pytest

from examkit.analyzer import Analyzer
from examkit.models import Finding, Result, Severity, Status, Subject
from examkit.modules.ferritin import FerritinAnalyzer
from examkit.modules.vitamin_d import VitaminDAnalyzer
from examkit.registry import Registry, RegistryError

ROOT = Path(__file__).parents[1]


def _load_tsh():
    path = ROOT / "examples" / "tsh.py"
    spec = importlib.util.spec_from_file_location("tsh_plugin", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_discover_loads_builtin_parts_only():
    registry = Registry.discover()
    assert [spec.id for spec in registry.specs()] == [
        "anemia_pattern",
        "ferritin",
        "hemoglobin",
        "vitamin_b12",
        "vitamin_d",
    ]
    assert all(spec.enabled for spec in registry.specs())
    assert "tsh" not in {spec.id for spec in registry.specs()}


def test_dropped_in_module_registers_only_classes_defined_there():
    module = ModuleType("plugin_extra")

    class Extra(Analyzer):
        id = "extra"
        description = "테스트 부품"
        codes = ("EXTRA",)

        def analyze_result(self, result: Result, subject: Subject) -> list[Finding]:
            return [
                Finding(
                    analyzer_id=self.id,
                    status=Status.NORMAL,
                    severity=Severity.INFO,
                    title="추가 부품",
                    summary="붙었습니다.",
                )
            ]

    Extra.__module__ = module.__name__
    module.VitaminDAnalyzer = VitaminDAnalyzer
    module.Extra = Extra
    module.Analyzer = Analyzer

    registry = Registry()
    registry.load_module(module)
    assert [analyzer.id for analyzer in registry] == ["extra"]


def test_manual_plugin_and_duplicate_id():
    module = _load_tsh()
    registry = Registry()
    registry.register(module.TshAnalyzer())
    assert registry.get("tsh").description.startswith("TSH")
    with pytest.raises(RegistryError, match="이미 등록된 부품"):
        registry.register(module.TshAnalyzer())


def test_entry_point_is_a_socket_for_external_parts():
    module = _load_tsh()

    class Entry:
        def load(self):
            return module.TshAnalyzer

    registry = Registry.discover(entry_points=[Entry()])
    assert registry.get("tsh").codes == ("TSH",)


def test_entry_point_cannot_reuse_a_builtin_id():
    class Entry:
        def load(self):
            return FerritinAnalyzer

    with pytest.raises(RegistryError, match="ferritin"):
        Registry.discover(entry_points=[Entry()])


def test_disable_unknown_and_invalid_id():
    registry = Registry.discover()
    with pytest.raises(RegistryError, match="없는 부품"):
        registry.disable("missing")

    class Bad(Analyzer):
        id = "Bad-ID"
        codes = ("X",)

    with pytest.raises(RegistryError, match="부품 id"):
        registry.register(Bad())


def test_core_does_not_import_concrete_parts():
    forbidden = ("vitamin_d", "vitamin_b12", "ferritin", "hemoglobin", "anemia_pattern")
    core = ROOT / "src" / "examkit"
    for path in core.glob("*.py"):
        text = path.read_text(encoding="utf-8")
        for name in forbidden:
            assert name not in text, path.name
