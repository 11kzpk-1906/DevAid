"""Tests for DevAid's CLI tools."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_explain_module_not_found() -> None:
    result = runner.invoke(
        app,
        ["explain", "ModuleNotFoundError: No module named 'requests'"],
    )

    assert result.exit_code == 0
    assert "ModuleNotFoundError" in result.output


def test_explain_unknown_error() -> None:
    result = runner.invoke(app, ["explain", "SomeUnknownError"])

    assert result.exit_code == 0
    assert "Unknown Error" in result.output


def test_analyze_python_project(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").touch()
    (tmp_path / "README.md").touch()
    (tmp_path / ".git").mkdir()

    result = runner.invoke(app, ["analyze", str(tmp_path)])

    assert result.exit_code == 0
    assert "Python" in result.output
    assert "README" in result.output
    assert "Git repository" in result.output


def test_analyze_invalid_directory(tmp_path: Path) -> None:
    invalid_path = tmp_path / "does-not-exist"

    result = runner.invoke(app, ["analyze", str(invalid_path)])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
