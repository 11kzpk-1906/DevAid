"""Tests for read-only Git Doctor diagnostics."""

import subprocess
from pathlib import Path

from devaid.diagnostics.git import inspect_git
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def _git(path: Path, *arguments: str) -> None:
    subprocess.run(
        ["git", *arguments],
        cwd=path,
        check=True,
        capture_output=True,
        text=True,
    )


def _create_repository(path: Path) -> None:
    _git(path, "init")
    _git(path, "config", "user.name", "DevAid Test")
    _git(path, "config", "user.email", "devaid-test@example.invalid")
    (path / "README.md").write_text("# Test repository\n", encoding="utf-8")
    _git(path, "add", "README.md")
    _git(path, "commit", "-m", "initial commit")


def test_git_doctor_reports_clean_repository_and_identity(tmp_path: Path) -> None:
    _create_repository(tmp_path)

    findings = inspect_git(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Repository"] == "PASS"
    assert statuses["Current branch"] == "PASS"
    assert statuses["Working tree"] == "PASS"
    assert statuses["Commit identity"] == "PASS"


def test_git_doctor_counts_staged_unstaged_and_untracked_changes(
    tmp_path: Path,
) -> None:
    _create_repository(tmp_path)
    (tmp_path / "README.md").write_text("# Updated\n", encoding="utf-8")
    (tmp_path / "staged.py").write_text("print('staged')\n", encoding="utf-8")
    (tmp_path / "untracked.py").write_text("print('new')\n", encoding="utf-8")
    _git(tmp_path, "add", "staged.py")

    findings = inspect_git(tmp_path)
    working_tree = next(details for area, _, details in findings if area == "Working tree")

    assert "1 staged" in working_tree
    assert "1 unstaged" in working_tree
    assert "1 untracked" in working_tree


def test_git_doctor_handles_directory_without_repository(tmp_path: Path) -> None:
    findings = inspect_git(tmp_path)

    assert findings == [
        ("Repository", "REVIEW", "This directory is not inside a Git repository")
    ]


def test_git_doctor_cli_displays_read_only_report(tmp_path: Path) -> None:
    _create_repository(tmp_path)

    result = runner.invoke(app, ["git", str(tmp_path)])

    assert result.exit_code == 0
    assert "DevAid Git Doctor" in result.output
    assert "Commit identity" in result.output
    assert "Read-only checks" in result.output


def test_git_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["git", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
