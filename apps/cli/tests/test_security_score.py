"""Tests for the local Security Score."""

import subprocess
from pathlib import Path

from devaid.diagnostics.security_score import evaluate_security_posture
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def _secure_project(root: Path) -> None:
    (root / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
    (root / "SECURITY.md").write_text("# Reporting vulnerabilities\n", encoding="utf-8")
    github = root / ".github"
    workflows = github / "workflows"
    workflows.mkdir(parents=True)
    (github / "dependabot.yml").write_text(
        "version: 2\nupdates: []\n", encoding="utf-8"
    )
    (workflows / "security.yml").write_text(
        "name: Security\non: [push]\njobs:\n  scan:\n    steps:\n"
        "      - uses: github/codeql-action/analyze@v3\n",
        encoding="utf-8",
    )
    (workflows / "tests.yml").write_text(
        "name: Tests\non: [push]\njobs: {}\n", encoding="utf-8"
    )
    (root / "app.py").write_text("print('safe')\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(root)], check=True)


def test_security_score_reports_full_baseline(tmp_path: Path) -> None:
    _secure_project(tmp_path)

    score, assessed, rows = evaluate_security_posture(tmp_path)

    assert score == 100
    assert assessed == 100
    assert all(row[1] == "PASS" for row in rows)


def test_security_score_deducts_for_missing_controls(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("value = eval(user_input)\n", encoding="utf-8")

    score, assessed, rows = evaluate_security_posture(tmp_path)

    assert assessed == 80  # Git and source controls are assessed; source exists.
    assert score < 100
    assert any(row[0] == "Dependabot" and row[1] == "REVIEW" for row in rows)
    assert any(row[0] == "Static source scan" and row[1] == "ERROR" for row in rows)


def test_security_score_detects_tracked_sensitive_file(tmp_path: Path) -> None:
    _secure_project(tmp_path)
    (tmp_path / ".env").write_text("TOKEN=not-printed\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp_path), "add", "-f", ".env"], check=True)

    score, assessed, rows = evaluate_security_posture(tmp_path)

    assert assessed == 100
    assert score < 100
    tracked = next(row for row in rows if row[0] == "Git-tracked sensitive files")
    assert tracked[1] == "ERROR"
    assert "1 sensitive-looking path" in tracked[4]


def test_security_score_cli_renders_report(tmp_path: Path) -> None:
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")

    result = runner.invoke(app, ["security-score", str(tmp_path)])

    assert result.exit_code == 0
    assert "Security posture score" in result.output
    assert "not a security certification" in result.output


def test_security_score_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["security-score", str(tmp_path / "missing")])
    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
