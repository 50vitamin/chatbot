"""분석 부품을 등록하고, 폴더와 진입점에서 찾아옵니다."""

from __future__ import annotations

import importlib
import pkgutil
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass
from types import ModuleType
from typing import Any

from examkit.analyzer import Analyzer

_PART_ID = re.compile(r"^[a-z][a-z0-9_]*$")


class RegistryError(Exception):
    """부품을 끼우거나 빼는 과정이 어긋날 때."""


@dataclass(frozen=True)
class AnalyzerSpec:
    id: str
    scope: str
    description: str
    codes: tuple[str, ...]
    names: tuple[str, ...]
    uses: tuple[str, ...]
    enabled: bool
    fallback: bool = False


class Registry:
    def __init__(self) -> None:
        self._items: dict[str, Analyzer] = {}
        self._disabled: set[str] = set()

    def register(self, analyzer: Analyzer) -> None:
        if not isinstance(analyzer, Analyzer) or type(analyzer) is Analyzer:
            raise RegistryError("분석 부품은 Analyzer의 구체 클래스 인스턴스여야 합니다.")
        if type(analyzer).__dict__.get("abstract", False):
            raise RegistryError(f"추상 부품은 등록할 수 없습니다: {analyzer.id or type(analyzer).__name__}")
        part_id = analyzer.id
        if not _PART_ID.fullmatch(part_id):
            raise RegistryError(
                f"부품 id는 소문자로 시작하는 영문, 숫자, 밑줄만 쓸 수 있습니다: {part_id!r}"
            )
        if analyzer.scope not in ("result", "panel"):
            raise RegistryError(f"{part_id} 부품의 scope는 result 또는 panel이어야 합니다.")
        owns_rows = bool(analyzer.codes) or analyzer.fallback or "matches" in type(analyzer).__dict__
        if analyzer.scope == "result" and not owns_rows:
            raise RegistryError(f"{part_id} 부품은 맡을 혈액검사 코드가 없습니다.")
        if part_id in self._items:
            raise RegistryError(f"이미 등록된 부품입니다: {part_id}")
        self._items[part_id] = analyzer
        self._disabled.discard(part_id)

    def register_loaded(self, loaded: Any) -> Analyzer:
        if isinstance(loaded, Analyzer):
            analyzer = loaded
        elif isinstance(loaded, type) and issubclass(loaded, Analyzer):
            analyzer = loaded()
        else:
            raise RegistryError("분석 부품은 Analyzer 클래스이거나 인스턴스여야 합니다.")
        self.register(analyzer)
        return analyzer

    def unregister(self, analyzer_id: str) -> None:
        if analyzer_id not in self._items:
            raise RegistryError(f"없는 부품입니다: {analyzer_id}")
        del self._items[analyzer_id]
        self._disabled.discard(analyzer_id)

    def disable(self, analyzer_id: str) -> None:
        if analyzer_id not in self._items:
            raise RegistryError(f"없는 부품입니다: {analyzer_id}")
        self._disabled.add(analyzer_id)

    def enable(self, analyzer_id: str) -> None:
        if analyzer_id not in self._items:
            raise RegistryError(f"없는 부품입니다: {analyzer_id}")
        self._disabled.discard(analyzer_id)

    def get(self, analyzer_id: str) -> Analyzer:
        try:
            return self._items[analyzer_id]
        except KeyError as exc:
            raise RegistryError(f"없는 부품입니다: {analyzer_id}") from exc

    def __iter__(self) -> Iterator[Analyzer]:
        return iter(self._items.values())

    def __len__(self) -> int:
        return len(self._items)

    def enabled(self) -> tuple[Analyzer, ...]:
        return tuple(
            analyzer for analyzer in self._items.values() if analyzer.id not in self._disabled
        )

    def specs(self) -> tuple[AnalyzerSpec, ...]:
        return tuple(
            AnalyzerSpec(
                id=analyzer.id,
                scope=analyzer.scope,
                description=analyzer.description,
                codes=tuple(analyzer.codes),
                names=tuple(analyzer.names),
                uses=tuple(analyzer.uses),
                enabled=analyzer.id not in self._disabled,
                fallback=analyzer.fallback,
            )
            for analyzer in sorted(self._items.values(), key=lambda item: item.id)
        )

    def load_module(self, module: ModuleType) -> None:
        for name in sorted(vars(module)):
            obj = getattr(module, name)
            if not _is_concrete_analyzer(obj):
                continue
            if obj.__module__ != module.__name__:
                continue
            self.register_loaded(obj)

    def load_package(self, package: ModuleType) -> None:
        infos = sorted(pkgutil.iter_modules(package.__path__), key=lambda item: item.name)
        for info in infos:
            if info.name.startswith("_"):
                continue
            module = importlib.import_module(f"{package.__name__}.{info.name}")
            self.load_module(module)

    @classmethod
    def discover(cls, entry_points: Sequence[Any] | None = None) -> Registry:
        """기본 부품 폴더와 ``examkit.analyzers`` 진입점을 끼웁니다."""

        registry = cls()
        from examkit import modules as builtin_modules

        registry.load_package(builtin_modules)
        discovered = _external_entry_points() if entry_points is None else entry_points
        for entry in discovered:
            loaded = entry.load() if hasattr(entry, "load") else entry
            registry.register_loaded(loaded)
        return registry


def _is_concrete_analyzer(obj: Any) -> bool:
    return (
        isinstance(obj, type)
        and issubclass(obj, Analyzer)
        and obj is not Analyzer
        and not obj.__dict__.get("abstract", False)
    )


def _external_entry_points() -> list[Any]:
    from importlib.metadata import entry_points

    return list(entry_points(group="examkit.analyzers"))
