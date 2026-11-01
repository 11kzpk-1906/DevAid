"""Tests for the new project-specific diagnostics and report export."""
import json
from pathlib import Path

from typer.testing import CliRunner

from devaid.diagnostics.javascript import inspect_javascript
from devaid.diagnostics.package_manager import inspect_packages
from devaid.diagnostics.python_project import inspect_python
from devaid.main import app

runner = CliRunner()


def test_package_manager_detects_multiple_js_lockfiles(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"sample"}', encoding="utf-8")
    (tmp_path / "package-lock.json").write_text("{}", encoding="utf-8")
    (tmp_path / "pnpm-lock.yaml").write_text("lockfileVersion: 9", encoding="utf-8")
    assert any("Multiple JavaScript" in item[1] for item in inspect_packages(tmp_path))


def test_python_doctor_detects_unpinned_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests\npytest==8.0\n", encoding="utf-8")
    assert any("Unpinned" in item[1] for item in inspect_python(tmp_path))


def test_javascript_doctor_reports_invalid_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text("{invalid", encoding="utf-8")
    assert inspect_javascript(tmp_path)[0][0] == "ERROR"


def test_javascript_doctor_checks_node_ignore(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"sample"}', encoding="utf-8")
    (tmp_path / ".gitignore").write_text("dist/\n", encoding="utf-8")
    titles = {item[1] for item in inspect_javascript(tmp_path)}
    assert "node_modules not ignored" in titles


def test_report_command_exports_json(tmp_path: Path) -> None:
    (tmp_path / "package.json").write_text('{"name":"sample"}', encoding="utf-8")
    target = tmp_path / "report.json"
    result = runner.invoke(app, ["report", str(tmp_path), "--format", "json", "--output", str(target)])
    assert result.exit_code == 0
    assert json.loads(target.read_text(encoding="utf-8"))["project"] == tmp_path.name
