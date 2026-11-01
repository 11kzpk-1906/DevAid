"""Tests for offline Release Doctor diagnostics."""

import json
import subprocess
from pathlib import Path

from devaid.diagnostics.release import inspect_release
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


def _release_project(path: Path) -> None:
    (path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "1.2.3"\n',
        encoding="utf-8",
    )
    (path / "package.json").write_text(
        json.dumps({"name": "sample", "version": "1.2.3"}),
        encoding="utf-8",
    )
    (path / "CHANGELOG.md").write_text(
        "# Changelog\n\n## [1.2.3] - 2026-11-01\n\n- Initial release\n",
        encoding="utf-8",
    )
    (path / "LICENSE").write_text("MIT License", encoding="utf-8")
    _git(path, "init")
    _git(path, "config", "user.name", "DevAid Test")
    _git(path, "config", "user.email", "devaid-test@example.invalid")
    (path / "README.md").write_text("# Sample\n", encoding="utf-8")
    _git(path, "add", ".")
    _git(path, "commit", "-m", "initial commit")
    _git(path, "tag", "v1.2.3")


def test_release_doctor_recognizes_release_metadata(tmp_path: Path) -> None:
    _release_project(tmp_path)

    findings = inspect_release(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Version metadata"] == "PASS"
    assert statuses["Version consistency"] == "PASS"
    assert statuses["Changelog"] == "PASS"
    assert statuses["License"] == "PASS"
    assert statuses["Git release tags"] == "PASS"


def test_release_doctor_flags_version_mismatch_and_missing_changelog(
    tmp_path: Path,
) -> None:
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )
    (tmp_path / "package.json").write_text(
        json.dumps({"name": "sample", "version": "2.0.0"}),
        encoding="utf-8",
    )

    findings = inspect_release(tmp_path)
    statuses = {area: status for area, status, _ in findings}

    assert statuses["Version consistency"] == "REVIEW"
    assert statuses["Changelog"] == "REVIEW"


def test_release_doctor_cli_prints_final_summary(tmp_path: Path) -> None:
    _release_project(tmp_path)

    result = runner.invoke(app, ["release", str(tmp_path)])

    assert result.exit_code == 0
    assert "Release Doctor" in result.output
    assert "Final summary:" in result.output
    assert "Offline readiness checks only" in " ".join(result.output.split())


def test_release_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["release", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
