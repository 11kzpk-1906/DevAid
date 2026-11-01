"""Tests for the offline Deployment Doctor command."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_deployment_checks_supported_files(tmp_path: Path) -> None:
    (tmp_path / "vercel.json").write_text('{"version": 2}', encoding="utf-8")
    (tmp_path / "netlify.toml").write_text('[build]\ncommand = "npm run build"\n', encoding="utf-8")
    dockerfile = "FROM python:3.12\nCMD [\"python\", \"app.py\"]\n"
    (tmp_path / "Dockerfile").write_text(dockerfile, encoding="utf-8")
    (tmp_path / "Procfile").write_text("web: python app.py\n", encoding="utf-8")

    result = runner.invoke(app, ["deploy", str(tmp_path)])

    assert result.exit_code == 0
    assert "Deployment Doctor" in result.output
    assert "vercel.json" in result.output
    assert "Dockerfile runtime" in result.output
    assert "does not deploy" in " ".join(result.output.split())


def test_deployment_reports_invalid_config_and_missing_runtime(tmp_path: Path) -> None:
    (tmp_path / "vercel.json").write_text("{invalid", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text("FROM python:3.12\n", encoding="utf-8")

    result = runner.invoke(app, ["deploy", str(tmp_path)])

    assert result.exit_code == 0
    assert "ERROR" in result.output
    assert "REVIEW" in result.output


def test_deployment_handles_no_detected_files(tmp_path: Path) -> None:
    result = runner.invoke(app, ["deploy", str(tmp_path)])

    assert result.exit_code == 0
    assert "No supported deployment files detected" in result.output


def test_deployment_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["deploy", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
