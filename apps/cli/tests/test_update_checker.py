from unittest.mock import MagicMock, patch
from urllib.error import HTTPError, URLError

from devaid.commands.update_checker import fetch_latest_release, version_key
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_version_key_orders_development_before_stable() -> None:
    assert version_key("0.2.0.dev0") < version_key("0.2.0")
    assert version_key("0.1.9") < version_key("0.2.0")


@patch("devaid.commands.update_checker.urlopen")
def test_fetch_latest_release_reads_github_response(mock_urlopen: MagicMock) -> None:
    response = MagicMock()
    response.__enter__.return_value.read.return_value = (
        b'{"tag_name":"v0.2.0","html_url":"https://github.com/11kzpk-1906/DevAid/releases/tag/v0.2.0"}'
    )
    mock_urlopen.return_value = response

    assert fetch_latest_release("11kzpk-1906/DevAid") == (
        "v0.2.0",
        "https://github.com/11kzpk-1906/DevAid/releases/tag/v0.2.0",
    )


@patch("devaid.commands.update_checker.urlopen")
def test_update_check_reports_newer_release(mock_urlopen: MagicMock) -> None:
    response = MagicMock()
    response.__enter__.return_value.read.return_value = (
        b'{"tag_name":"v0.2.0","html_url":"https://example.com/release"}'
    )
    mock_urlopen.return_value = response

    result = runner.invoke(app, ["update-check"])
    assert result.exit_code == 0
    assert "A newer release is available" in result.output
    assert "does not install anything" in result.output


@patch("devaid.commands.update_checker.urlopen")
def test_update_check_handles_network_failure(mock_urlopen: MagicMock) -> None:
    mock_urlopen.side_effect = URLError("offline")

    result = runner.invoke(app, ["update-check"])
    assert result.exit_code == 0
    assert "Could not check for updates" in result.output
