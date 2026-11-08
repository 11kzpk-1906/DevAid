from __future__ import annotations

import json
import zipfile
from pathlib import Path

import pytest

from devaid.commands.backup import (
    MANIFEST_NAME,
    backup_project,
    restore_backup,
    verify_backup,
)


def test_backup_excludes_generated_and_sensitive_files(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / "src").mkdir(parents=True)
    (project / ".venv").mkdir()
    (project / "node_modules").mkdir()
    (project / "src" / "app.py").write_text("print('hello')", encoding="utf-8")
    (project / ".env").write_text("TOKEN=secret", encoding="utf-8")
    (project / ".env.example").write_text("TOKEN=replace-me", encoding="utf-8")
    (project / ".venv" / "ignored.txt").write_text("ignored", encoding="utf-8")
    (project / "node_modules" / "ignored.js").write_text("ignored", encoding="utf-8")

    archive = backup_project(project)
    assert archive.exists()
    with zipfile.ZipFile(archive) as zipped:
        names = set(zipped.namelist())
    assert "src/app.py" in names
    assert ".env.example" in names
    assert ".env" not in names
    assert ".venv/ignored.txt" not in names
    assert "node_modules/ignored.js" not in names
    assert verify_backup(archive) == 2


def test_backup_refuses_to_overwrite_existing_archive(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    archive = tmp_path / "backup.zip"
    archive.write_text("keep", encoding="utf-8")
    with pytest.raises(FileExistsError):
        backup_project(project, archive)
    assert archive.read_text(encoding="utf-8") == "keep"


def test_restore_creates_files_and_refuses_existing_destination(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "hello.txt").write_text("hello", encoding="utf-8")
    archive = backup_project(project, tmp_path / "backup.zip")

    destination = tmp_path / "restored"
    assert restore_backup(archive, destination) == 1
    assert (destination / "hello.txt").read_text(encoding="utf-8") == "hello"
    with pytest.raises(FileExistsError):
        restore_backup(archive, destination)


def test_verify_detects_modified_archive_content(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "hello.txt").write_text("hello", encoding="utf-8")
    archive = backup_project(project, tmp_path / "backup.zip")

    tampered_archive = tmp_path / "tampered.zip"
    with zipfile.ZipFile(archive, "r") as original:
        manifest_data = original.read(MANIFEST_NAME)
    with zipfile.ZipFile(tampered_archive, "w") as tampered:
        tampered.writestr("hello.txt", "changed")
        tampered.writestr(MANIFEST_NAME, manifest_data)

    with pytest.raises(ValueError, match="integrity"):
        verify_backup(tampered_archive)


EMPTY_SHA256 = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"


def test_verify_rejects_path_traversal(tmp_path: Path) -> None:
    archive = tmp_path / "unsafe.zip"
    manifest = {
        "format": 1,
        "files": [
            {
                "path": "../outside.txt",
                "size": 0,
                "sha256": EMPTY_SHA256,
            }
        ],
    }
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("../outside.txt", "")
        zipped.writestr(MANIFEST_NAME, json.dumps(manifest))
    with pytest.raises(ValueError, match="unsafe"):
        verify_backup(archive)


def test_verify_rejects_windows_drive_path(tmp_path: Path) -> None:
    archive = tmp_path / "windows-path.zip"
    manifest = {
        "format": 1,
        "files": [
            {
                "path": "C:/outside.txt",
                "size": 0,
                "sha256": EMPTY_SHA256,
            }
        ],
    }
    with zipfile.ZipFile(archive, "w") as zipped:
        zipped.writestr("C:/outside.txt", "")
        zipped.writestr(MANIFEST_NAME, json.dumps(manifest))
    with pytest.raises(ValueError, match="unsafe"):
        verify_backup(archive)
