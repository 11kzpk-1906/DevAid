"""Tests for the offline Dependency Doctor command."""

import json
from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_deps_reads_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\n'
        'dependencies = ["typer>=0.15", "rich>=13.9"]\n'
        '[project.optional-dependencies]\n'
        'dev = ["pytest>=8"]\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["deps", str(tmp_path)])

    assert result.exit_code == 0
    assert "pyproject.toml" in result.output
    assert "2 production" in result.output
    assert "1 development" in result.output
    assert "Offline inspection only" in result.output


def test_deps_reads_node_project(tmp_path: Path) -> None:
    manifest = {
        "dependencies": {"react": "^19.0.0"},
        "devDependencies": {"vite": "^7.0.0"},
    }
    (tmp_path / "package.json").write_text(
        json.dumps(manifest),
        encoding="utf-8",
    )

    result = runner.invoke(app, ["deps", str(tmp_path)])

    assert result.exit_code == 0
    assert "package.json" in result.output
    assert "1 production" in result.output
    assert "1 development" in result.output


def test_deps_handles_missing_manifests(tmp_path: Path) -> None:
    result = runner.invoke(app, ["deps", str(tmp_path)])

    assert result.exit_code == 0
    assert "No supported dependency manifests found" in result.output


def test_deps_rejects_invalid_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"

    result = runner.invoke(app, ["deps", str(missing)])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
