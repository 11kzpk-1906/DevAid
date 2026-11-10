from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from devaid.main import app

runner = CliRunner()


def test_backup_verify_and_restore_full_cli_workflow(tmp_path: Path) -> None:
    project = tmp_path / "sample"
    (project / "src").mkdir(parents=True)
    (project / "src" / "app.py").write_text("print('hello')\n", encoding="utf-8")
    (project / ".env").write_text("TOKEN=do-not-back-up\n", encoding="utf-8")
    archive = tmp_path / "sample-backup.zip"

    created = runner.invoke(
        app,
        ["backup", "--path", str(project), "--output", str(archive)],
    )
    assert created.exit_code == 0
    assert "Backup created" in created.output
    assert archive.is_file()

    verified = runner.invoke(app, ["backup-verify", str(archive)])
    assert verified.exit_code == 0
    assert "Backup verified" in verified.output
    assert "1 files" in verified.output

    destination = tmp_path / "restored"
    restored = runner.invoke(
        app,
        ["restore", str(archive), "--destination", str(destination)],
    )
    assert restored.exit_code == 0
    assert "Restored 1 files" in restored.output
    assert (destination / "src" / "app.py").read_text(encoding="utf-8") == "print('hello')\n"
    assert not (destination / ".env").exists()


def test_backup_restore_cli_reports_invalid_inputs(tmp_path: Path) -> None:
    missing_project = tmp_path / "does-not-exist"
    backup = runner.invoke(
        app,
        ["backup", "--path", str(missing_project), "--output", str(tmp_path / "bad.zip")],
    )
    assert backup.exit_code != 0
    assert "Backup failed" in backup.output

    missing_archive = runner.invoke(app, ["backup-verify", str(tmp_path / "missing.zip")])
    assert missing_archive.exit_code != 0
    assert "Backup verification failed" in missing_archive.output

    project = tmp_path / "project"
    project.mkdir()
    (project / "file.txt").write_text("content", encoding="utf-8")
    archive_path = tmp_path / "valid.zip"
    assert runner.invoke(
        app,
        ["backup", "--path", str(project), "--output", str(archive_path)],
    ).exit_code == 0

    existing_destination = tmp_path / "already-there"
    existing_destination.mkdir()
    (existing_destination / "keep.txt").write_text("keep", encoding="utf-8")
    restore = runner.invoke(
        app,
        ["restore", str(archive_path), "--destination", str(existing_destination)],
    )
    assert restore.exit_code != 0
    assert "Restore failed" in restore.output
    assert (existing_destination / "keep.txt").read_text(encoding="utf-8") == "keep"


def test_snapshot_and_compare_cli_classify_project_changes(tmp_path: Path) -> None:
    before = tmp_path / "before"
    after = tmp_path / "after"
    before.mkdir()
    after.mkdir()

    (before / "unchanged.txt").write_text("same", encoding="utf-8")
    (before / "modified.txt").write_text("old", encoding="utf-8")
    (before / "deleted.txt").write_text("remove", encoding="utf-8")
    (after / "unchanged.txt").write_text("same", encoding="utf-8")
    (after / "modified.txt").write_text("new", encoding="utf-8")
    (after / "added.txt").write_text("added", encoding="utf-8")

    before_snapshot = tmp_path / "before.json"
    after_snapshot = tmp_path / "after.json"

    for project, output in ((before, before_snapshot), (after, after_snapshot)):
        result = runner.invoke(
            app,
            ["snapshot", "--path", str(project), "--output", str(output)],
        )
        assert result.exit_code == 0
        assert "Snapshot created" in result.output
        assert output.is_file()

    compared = runner.invoke(
        app,
        ["snapshot-compare", str(before_snapshot), str(after_snapshot)],
    )
    assert compared.exit_code == 0
    assert "Added (1)" in compared.output
    assert "added.txt" in compared.output
    assert "Modified (1)" in compared.output
    assert "modified.txt" in compared.output
    assert "Deleted (1)" in compared.output
    assert "deleted.txt" in compared.output
    assert "Unchanged (1)" in compared.output
    assert "unchanged.txt" in compared.output


def test_snapshot_cli_reports_invalid_inputs(tmp_path: Path) -> None:
    missing_project = tmp_path / "does-not-exist"
    snapshot = runner.invoke(
        app,
        ["snapshot", "--path", str(missing_project), "--output", str(tmp_path / "bad.json")],
    )
    assert snapshot.exit_code != 0
    assert "Snapshot failed" in snapshot.output

    compare = runner.invoke(
        app,
        ["snapshot-compare", str(tmp_path / "missing-before.json"), str(tmp_path / "missing-after.json")],
    )
    assert compare.exit_code != 0
    assert "Snapshot comparison failed" in compare.output
