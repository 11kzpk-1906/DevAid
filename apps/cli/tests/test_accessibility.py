"""Tests for offline Accessibility Doctor checks."""

from pathlib import Path

from devaid.diagnostics.accessibility import inspect_accessibility
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_accessibility_doctor_detects_common_html_issues(tmp_path: Path) -> None:
    page = """
    <html>
      <head><title>Sample page</title></head>
      <body>
        <img src="photo.png">
        <input id="email" type="email">
        <a href="/next"></a>
        <button></button>
      </body>
    </html>
    """
    (tmp_path / "index.html").write_text(page, encoding="utf-8")

    findings = inspect_accessibility(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Images"] == "REVIEW"
    assert statuses["Form controls"] == "REVIEW"
    assert statuses["Links"] == "REVIEW"
    assert statuses["Buttons"] == "REVIEW"
    assert statuses["Document language"] == "REVIEW"
    assert statuses["Document title"] == "PASS"


def test_accessibility_doctor_accepts_basic_accessible_markup(tmp_path: Path) -> None:
    page = """
    <html lang="en">
      <head><title>Accessible page</title></head>
      <body>
        <img src="photo.png" alt="A landscape">
        <label for="email">Email</label>
        <input id="email" type="email">
        <a href="/next">Continue</a>
        <button type="button">Save</button>
      </body>
    </html>
    """
    (tmp_path / "index.html").write_text(page, encoding="utf-8")

    findings = inspect_accessibility(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Images"] == "PASS"
    assert statuses["Form controls"] == "PASS"
    assert statuses["Links"] == "PASS"
    assert statuses["Buttons"] == "PASS"
    assert statuses["Document language"] == "PASS"
    assert statuses["Document title"] == "PASS"


def test_accessibility_doctor_reports_no_html_files(tmp_path: Path) -> None:
    findings = inspect_accessibility(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["HTML coverage"] == "INFO"
    assert statuses["Accessibility scan"] == "INFO"


def test_accessibility_doctor_cli_prints_final_summary(tmp_path: Path) -> None:
    (tmp_path / "index.html").write_text(
        '<html lang="en"><head><title>Test</title></head></html>',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["accessibility", str(tmp_path)])

    assert result.exit_code == 0
    assert "Accessibility Doctor" in result.output
    assert "Final summary:" in result.output
    assert "Static HTML checks only" in " ".join(result.output.split())


def test_accessibility_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["accessibility", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
