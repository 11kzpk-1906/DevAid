"""Tests for DevAid Fix Suggestions."""

from pathlib import Path

from devaid.diagnostics.suggestions import collect_suggestions
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_suggestions_identify_common_project_gaps(tmp_path: Path) -> None:
    findings = collect_suggestions(tmp_path)

    titles = {title for _, title, _ in findings}
    assert "Add a README" in titles
    assert "Add automated tests" in titles
    assert "Add a .gitignore" in titles
    assert "Add continuous integration" in titles
    assert "Add contribution guidance" in titles


def test_suggestions_respect_existing_project_files(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Project\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(
        ".env\n.venv/\nnode_modules/\n", encoding="utf-8"
    )
    (tmp_path / "tests").mkdir()
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: CI\n", encoding="utf-8")
    (tmp_path / "CONTRIBUTING.md").write_text("# Contributing\n", encoding="utf-8")

    findings = collect_suggestions(tmp_path)
    titles = {title for _, title, _ in findings}

    assert "Add a README" not in titles
    assert "Add automated tests" not in titles
    assert "Add a .gitignore" not in titles
    assert "Add continuous integration" not in titles
    assert "Add contribution guidance" not in titles


def test_suggestions_command_displays_recommendations(tmp_path: Path) -> None:
    result = runner.invoke(app, ["suggest", str(tmp_path)])

    assert result.exit_code == 0
    assert "DevAid Fix Suggestions" in result.output
    assert "Add a README" in result.output
    assert "never applies them automatically" in result.output
