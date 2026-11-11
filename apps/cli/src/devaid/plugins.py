from importlib.metadata import EntryPoint, entry_points
from pathlib import Path

PLUGIN_GROUP = "devaid.analyzers"


def discover_analyzer_plugins() -> list[EntryPoint]:
    """Return installed analyzer entry points without importing plugin code."""
    return sorted(entry_points(group=PLUGIN_GROUP), key=lambda plugin: plugin.name)


def run_analyzer_plugin(name: str, path: Path) -> None:
    """Load and run one explicitly selected analyzer plugin."""
    plugin = next(
        (item for item in discover_analyzer_plugins() if item.name == name),
        None,
    )
    if plugin is None:
        available = ", ".join(item.name for item in discover_analyzer_plugins())
        raise LookupError(
            f"Analyzer plugin {name!r} was not found. Available plugins: "
            f"{available or 'none'}"
        )

    callback = plugin.load()
    if not callable(callback):
        raise TypeError(
            f"Plugin {name!r} must expose a callable accepting one pathlib.Path."
        )
    callback(path)
