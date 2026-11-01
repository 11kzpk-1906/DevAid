"""Tests for the offline Config Doctor command."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_config_checks_common_files(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(
        ".env\n.venv/\n__pycache__/\nnode_modules/\n", encoding="utf-8"
    )
    (tmp_path / ".editorconfig").write_text(
        "root = true\n[*]\nindent_style = space\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text("[project]\nname = 'demo'\n", encoding="utf-8")
    (tmp_path / "package.json").write_text('{"name": "demo"}', encoding="utf-8")

    result = runner.invoke(app, ["config", str(tmp_path)])

    assert result.exit_code == 0
    assert "DevAid Config Doctor" in result.output
    assert "pyproject.toml" in result.output
    assert "package.json" in result.output
    assert "4 passed" in result.output
    assert "never reads .env contents" in " ".join(result.output.split())


def test_config_reports_invalid_manifests(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text("[project", encoding="utf-8")
    (tmp_path / "package.json").write_text("{invalid", encoding="utf-8")

    result = runner.invoke(app, ["config", str(tmp_path)])

    assert result.exit_code == 0
    assert "ERROR" in result.output
    assert "pyproject.toml" in result.output
    assert "package.json" in result.output


def test_config_recommends_env_template_without_reading_env(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TOKEN=do-not-read", encoding="utf-8")

    result = runner.invoke(app, ["config", str(tmp_path)])

    assert result.exit_code == 0
    assert ".env.example" in result.output
    assert "Add a template" in result.output
    assert "do-not-read" not in result.output


def test_config_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["config", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
