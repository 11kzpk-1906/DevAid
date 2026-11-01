"""Tests for the offline GitHub Actions Workflow Doctor."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_workflow_doctor_reports_permissions_and_unpinned_actions(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "name: CI\non: [push]\njobs:\n  test:\n    steps:\n"
        "      - uses: actions/checkout@v4\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["workflow-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "Workflow Doctor" in result.output
    assert "Declare least-privilege permissions explicitly" in result.output
    assert "full commit SHA" in result.output
    assert "persist-credentials: false" in result.output


def test_workflow_doctor_accepts_explicit_permissions_and_sha_pins(
    tmp_path: Path,
) -> None:
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    sha = "a" * 40
    (workflow_dir / "ci.yaml").write_text(
        "name: CI\npermissions:\n  contents: read\njobs:\n"
        f"  test:\n    steps:\n      - uses: actions/checkout@{sha}\n"
        "        with:\n          persist-credentials: false\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["workflow-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "Explicit workflow or job permissions are declared" in result.output
    assert "pinned to full commit SHAs" in result.output
    assert "items to review" in result.output
    assert "0 items to review" in " ".join(result.output.split())


def test_workflow_doctor_handles_missing_workflows(tmp_path: Path) -> None:
    result = runner.invoke(app, ["workflow-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "No GitHub Actions workflows found" in result.output


def test_workflow_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["workflow-doctor", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
