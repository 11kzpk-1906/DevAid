"""Tests for the local Environment Doctor command."""

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_environment_reports_python_runtime() -> None:
    result = runner.invoke(app, ["env"])

    assert result.exit_code == 0
    assert "Environment Doctor" in result.output
    assert "Python runtime" in result.output
    assert "Operating system" in result.output
    assert "does not install" in " ".join(result.output.split())


def test_environment_reports_tool_availability(monkeypatch) -> None:
    from devaid.diagnostics import environment

    monkeypatch.setattr(environment.shutil, "which", lambda tool: None)
    monkeypatch.setattr(environment, "find_spec", lambda name: None)

    result = runner.invoke(app, ["env"])

    assert result.exit_code == 0
    assert "uv" in result.output
    assert "node" in result.output
    assert "Not detected on PATH" in result.output
