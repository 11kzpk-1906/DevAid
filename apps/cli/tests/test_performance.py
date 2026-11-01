"""Tests for offline Performance Doctor diagnostics."""

import json
from pathlib import Path

from devaid.diagnostics.performance import inspect_performance
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_performance_doctor_detects_build_and_lockfile(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"build": "vite build"}}),
        encoding="utf-8",
    )
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: '9.0'\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(
        ".venv\nvenv\n__pycache__\nnode_modules\ndist\nbuild\n",
        encoding="utf-8",
    )

    findings = inspect_performance(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Node build setup"] == "PASS"
    assert statuses["Dependency reproducibility"] == "PASS"
    assert statuses["Generated files"] == "PASS"
    assert statuses["Scan coverage"] == "PASS"


def test_performance_doctor_reports_missing_build_setup(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name": "sample"}', encoding="utf-8")

    findings = inspect_performance(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Node build setup"] == "REVIEW"
    assert statuses["Dependency reproducibility"] == "REVIEW"


def test_performance_doctor_handles_invalid_package_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{invalid", encoding="utf-8")

    findings = inspect_performance(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Node build setup"] == "ERROR"


def test_performance_doctor_cli_prints_final_summary(tmp_path: Path) -> None:
    result = runner.invoke(app, ["performance", str(tmp_path)])

    assert result.exit_code == 0
    assert "Performance Doctor" in result.output
    assert "Final summary:" in result.output
    assert "Static checks only" in " ".join(result.output.split())


def test_performance_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["performance", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
