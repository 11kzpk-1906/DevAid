"""Tests for the offline project health report."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_health_reports_project_checks(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Sample", encoding="utf-8")
    (tmp_path / ".git").mkdir()
    (tmp_path / "pyproject.toml").write_text("[project]", encoding="utf-8")
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "test_sample.py").write_text(
        "def test_sample(): pass", encoding="utf-8"
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing", encoding="utf-8")

    result = runner.invoke(app, ["health", str(tmp_path)])

    assert result.exit_code == 0
    assert "Project Health" in result.output
    assert "100/100" in result.output
    assert "6/6 checks passed" in result.output
    normalized_output = " ".join(result.output.split())
    assert "not a security audit" in normalized_output


def test_health_flags_missing_project_basics(tmp_path: Path) -> None:
    result = runner.invoke(app, ["health", str(tmp_path)])

    assert result.exit_code == 0
    assert "0/100" in result.output
    assert "Needs work" in result.output


def test_health_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["health", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
