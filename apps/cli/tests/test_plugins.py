from collections.abc import Callable
from pathlib import Path

import pytest

from devaid import plugins


class FakeEntryPoint:
    name = "sample"

    def __init__(self, callback: Callable[[Path], None]) -> None:
        self.callback = callback

    def load(self) -> Callable[[Path], None]:
        return self.callback


def test_run_analyzer_plugin_calls_selected_entry_point(monkeypatch) -> None:
    calls: list[Path] = []
    entry = FakeEntryPoint(calls.append)
    monkeypatch.setattr(plugins, "discover_analyzer_plugins", lambda: [entry])

    target = Path("sample-project")
    plugins.run_analyzer_plugin("sample", target)

    assert calls == [target]


def test_run_analyzer_plugin_rejects_unknown_name(monkeypatch) -> None:
    monkeypatch.setattr(plugins, "discover_analyzer_plugins", lambda: [])

    with pytest.raises(LookupError, match="was not found"):
        plugins.run_analyzer_plugin("missing", Path("."))


def test_run_analyzer_plugin_rejects_non_callable(monkeypatch) -> None:
    entry = FakeEntryPoint(None)
    monkeypatch.setattr(plugins, "discover_analyzer_plugins", lambda: [entry])

    with pytest.raises(TypeError, match="must expose a callable"):
        plugins.run_analyzer_plugin("sample", Path("."))
