from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "0.2.0.dev0" in result.output


def test_help_command() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "developer" in result.output.lower()


