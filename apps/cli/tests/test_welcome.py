from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_welcome_quit() -> None:
    result = runner.invoke(app, ["welcome"], input="quit\n")
    assert result.exit_code == 0
    assert "Welcome to DevAid" in result.output
    assert "menu closed" in result.output


def test_welcome_rejects_invalid_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    result = runner.invoke(app, ["welcome", str(missing)], input="quit\n")
    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
