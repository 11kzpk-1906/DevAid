"""Public, versioned contracts for third-party DevAid analyzer plugins."""
from __future__ import annotations

import inspect
import tomllib
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

PLUGIN_API_VERSION = 1


@dataclass(frozen=True)
class AnalyzerFinding:
    rule_id: str
    severity: str
    message: str
    path: str | None = None
    line: int | None = None


@dataclass(frozen=True)
class AnalyzerResult:
    findings: tuple[AnalyzerFinding, ...] = ()
    summary: str = ""


@dataclass(frozen=True)
class PluginManifest:
    name: str
    api_version: int
    entry_point: str


def parse_plugin_manifest(content: str) -> PluginManifest:
    """Parse and validate a TOML manifest without importing plugin code."""
    try:
        data = tomllib.loads(content)
    except tomllib.TOMLDecodeError as error:
        raise ValueError(f"invalid plugin manifest TOML: {error}") from error
    manifest = data.get("devaid-plugin")
    if not isinstance(manifest, dict):
        raise ValueError("manifest must contain a [devaid-plugin] table")
    name, api_version, entry_point = (
        manifest.get("name"), manifest.get("api-version"), manifest.get("entry-point")
    )
    if not isinstance(name, str) or not name.strip():
        raise ValueError("plugin name must be a non-empty string")
    if not isinstance(api_version, int):
        raise ValueError("plugin api-version must be an integer")
    if api_version != PLUGIN_API_VERSION:
        raise ValueError(
            f"unsupported plugin API version {api_version}; expected {PLUGIN_API_VERSION}"
        )
    if not isinstance(entry_point, str) or ":" not in entry_point:
        raise ValueError("entry-point must use package.module:callable syntax")
    return PluginManifest(name.strip(), api_version, entry_point)


def validate_entry_point_metadata(entry_point: object) -> PluginManifest | None:
    """Validate an installed plugin manifest before importing its entry-point code.

    Older entry-point-only plugins remain supported as a compatibility path.
    """
    distribution = getattr(entry_point, "dist", None)
    reader = getattr(distribution, "read_text", None)
    if not callable(reader):
        return None
    content = reader("devaid-plugin.toml")
    if not content:
        return None
    manifest = parse_plugin_manifest(content)
    if manifest.name != getattr(entry_point, "name", None):
        raise ValueError("plugin manifest name does not match its entry-point name")
    if manifest.entry_point != getattr(entry_point, "value", None):
        raise ValueError("plugin manifest entry-point does not match installed metadata")
    return manifest


def validate_analyzer(callback: Callable[..., object]) -> None:
    """Validate a plugin callback's shape without invoking it."""
    if not callable(callback):
        raise TypeError("Plugin must expose a callable accepting one pathlib.Path.")
    try:
        signature = inspect.signature(callback)
        signature.bind(Path("."))
    except (TypeError, ValueError) as error:
        raise TypeError("analyzer must accept one pathlib.Path argument") from error
