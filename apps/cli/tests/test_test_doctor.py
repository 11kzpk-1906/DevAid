"""Tests for the offline Test Doctor."""

import json
from pathlib import Path

from devaid.diagnostics.test_doctor import inspect_tests
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_python_test_readiness(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n'
        '[tool.pytest.ini_options]\ntestpaths = ["tests"]\n',
        encoding="utf-8",
    )
    tests = tmp_path / "tests"
    tests.mkdir()
    (tests / "test_sample.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")

    findings = inspect_tests(tmp_path)
    results = {area: status for area, status, _ in findings}

    assert results["Python tests"] == "PASS"
    assert results["Python test runner"] == "PASS"


def test_javascript_test_readiness(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text(
        json.dumps({"scripts": {"test": "vitest run"}, "devDependencies": {"vitest": "*"}}),
        encoding="utf-8",
    )
    source = tmp_path / "src"
    source.mkdir()
    (source / "app.test.ts").write_text("test('works', () => {});", encoding="utf-8")

    findings = inspect_tests(tmp_path)
    results = {area: status for area, status, _ in findings}

    assert results["JavaScript test script"] == "PASS"
    assert results["JavaScript test files"] == "PASS"


def test_go_test_files_are_detected(tmp_path: Path) -> None:
    (tmp_path / "go.mod").write_text("module example.com/demo\n", encoding="utf-8")
    (tmp_path / "main_test.go").write_text("package main\n", encoding="utf-8")

    findings = inspect_tests(tmp_path)
    assert ("Go tests", "PASS", "Go test files detected") in findings


def test_ci_without_test_command_is_flagged(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )
    workflows = tmp_path / ".github" / "workflows"
    workflows.mkdir(parents=True)
    (workflows / "ci.yml").write_text("name: Build\njobs: {}\n", encoding="utf-8")

    findings = inspect_tests(tmp_path)
    assert any(
        area == "CI test step" and status == "REVIEW"
        for area, status, _ in findings
    )


def test_test_doctor_command_is_read_only(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "0.1.0"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["test-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "DevAid Test Doctor" in result.output
    assert "does not run tests" in " ".join(result.output.split())


def test_test_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["test-doctor", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
