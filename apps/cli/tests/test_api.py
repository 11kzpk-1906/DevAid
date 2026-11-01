"""Tests for the read-only API Doctor command."""

from email.message import Message
from io import BytesIO
from urllib.error import URLError

from devaid.diagnostics import api
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


class FakeResponse:
    def __init__(self, body: bytes, status: int = 200, content_type: str = "application/json"):
        self.status = status
        self.headers = Message()
        self.headers["Content-Type"] = content_type
        self.headers["Strict-Transport-Security"] = "max-age=31536000"
        self.body = BytesIO(body)

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self, size: int = -1) -> bytes:
        return self.body.read(size)


def test_api_reports_valid_json_response(monkeypatch) -> None:
    monkeypatch.setattr(api, "urlopen", lambda *_args, **_kwargs: FakeResponse(b'{"ok": true}'))

    result = runner.invoke(app, ["api", "https://example.com/status"])

    assert result.exit_code == 0
    assert "200" in result.output
    assert "Valid JSON" in result.output
    assert "Strict-Transport-Security" in result.output
    assert "does not submit data" in " ".join(result.output.split())


def test_api_reports_invalid_json(monkeypatch) -> None:
    monkeypatch.setattr(api, "urlopen", lambda *_args, **_kwargs: FakeResponse(b"{bad"))

    result = runner.invoke(app, ["api", "https://example.com/status"])

    assert result.exit_code == 0
    assert "Invalid JSON" in result.output


def test_api_rejects_invalid_url() -> None:
    result = runner.invoke(app, ["api", "file:///etc/passwd"])

    assert result.exit_code == 2
    assert "Invalid URL" in result.output


def test_api_handles_connection_error(monkeypatch) -> None:
    def fail(*_args, **_kwargs):
        raise URLError("connection refused")

    monkeypatch.setattr(api, "urlopen", fail)

    result = runner.invoke(app, ["api", "https://example.com/status"])

    assert result.exit_code == 1
    assert "Could not reach the endpoint" in result.output
