from pathlib import Path

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


def test_backup_verify_and_restore_commands(tmp_path: Path) -> None:
    project = tmp_path / "sample"
    project.mkdir()
    (project / "hello.txt").write_text("hello", encoding="utf-8")
    archive = tmp_path / "sample.zip"
    backup_result = runner.invoke(
        app,
        ["backup", "--path", str(project), "--output", str(archive)],
    )
    assert backup_result.exit_code == 0
    assert "Backup created" in backup_result.output

    verify_result = runner.invoke(app, ["backup-verify", str(archive)])
    assert verify_result.exit_code == 0
    assert "Backup verified" in verify_result.output

    destination = tmp_path / "restored"
    restore_result = runner.invoke(
        app,
        ["restore", str(archive), "--destination", str(destination)],
    )
    assert restore_result.exit_code == 0
    assert (destination / "hello.txt").read_text(encoding="utf-8") == "hello"


def test_snapshot_commands(tmp_path: Path) -> None:
    from devaid.main import app

    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()
    (before / "same.txt").write_text("same", encoding="utf-8")
    (after / "same.txt").write_text("same", encoding="utf-8")
    (after / "new.txt").write_text("new", encoding="utf-8")
    before_snapshot = tmp_path / "before.json"
    after_snapshot = tmp_path / "after.json"

    first = runner.invoke(
        app,
        ["snapshot", "--path", str(before), "--output", str(before_snapshot)],
    )
    second = runner.invoke(
        app,
        ["snapshot", "--path", str(after), "--output", str(after_snapshot)],
    )
    assert first.exit_code == 0
    assert second.exit_code == 0

    compared = runner.invoke(
        app,
        ["snapshot-compare", str(before_snapshot), str(after_snapshot)],
    )
    assert compared.exit_code == 0
    assert "Added (1)" in compared.output
    assert "new.txt" in compared.output
    assert "Unchanged (1)" in compared.output
