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
    assert "Frameworks" in result.output
    assert "Package managers" in result.output


def test_analyze_detects_framework_and_package_manager(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        '{"dependencies": {"react": "^19.0.0", "next": "^15.0.0"}}',
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")

    result = runner.invoke(app, ["analyze", str(tmp_path)])

    assert result.exit_code == 0
    assert "React" in result.output
    assert "Next.js" in result.output
    assert "pnpm" in result.output


def test_analyze_detects_python_framework(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text(
        "fastapi>=0.100\nuvicorn>=0.20\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["analyze", str(tmp_path)])

    assert result.exit_code == 0
    assert "FastAPI" in result.output


def test_analyze_invalid_directory(tmp_path: Path) -> None:
    invalid_path = tmp_path / "does-not-exist"

    result = runner.invoke(app, ["analyze", str(invalid_path)])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
