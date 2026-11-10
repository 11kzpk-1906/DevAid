from __future__ import annotations

import json
from pathlib import Path

import pytest
from devaid.commands.snapshot import compare_snapshots, create_snapshot


def test_snapshot_records_files_and_hashes(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "hello.txt").write_text("hello", encoding="utf-8")
    output = tmp_path / "first.json"

    assert create_snapshot(project, output) == output
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["format"] == 1
    assert payload["files"]["hello.txt"]["size"] == 5
    assert len(payload["files"]["hello.txt"]["sha256"]) == 64


def test_snapshot_excludes_secrets_and_generated_directories(tmp_path: Path) -> None:
    project = tmp_path / "project"
    (project / ".venv").mkdir(parents=True)
    (project / "node_modules").mkdir()
    (project / "src").mkdir()
    (project / ".env").write_text("secret", encoding="utf-8")
    (project / "src" / ".env.example").write_text("template", encoding="utf-8")
    (project / ".venv" / "cache.py").write_text("ignored", encoding="utf-8")
    (project / "node_modules" / "package.js").write_text("ignored", encoding="utf-8")

    output = tmp_path / "snapshot.json"
    create_snapshot(project, output)
    names = json.loads(output.read_text(encoding="utf-8"))["files"]
    assert "src/.env.example" in names
    assert ".env" not in names
    assert ".venv/cache.py" not in names
    assert "node_modules/package.js" not in names


def test_snapshot_refuses_to_overwrite_output(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    output = tmp_path / "snapshot.json"
    output.write_text("keep", encoding="utf-8")

    with pytest.raises(FileExistsError):
        create_snapshot(project, output)
    assert output.read_text(encoding="utf-8") == "keep"


def test_compare_classifies_added_modified_deleted_and_unchanged(tmp_path: Path) -> None:
    before_project = tmp_path / "before"
    after_project = tmp_path / "after"
    before_project.mkdir()
    after_project.mkdir()
    (before_project / "same.txt").write_text("same", encoding="utf-8")
    (before_project / "change.txt").write_text("old", encoding="utf-8")
    (before_project / "remove.txt").write_text("remove", encoding="utf-8")
    (after_project / "same.txt").write_text("same", encoding="utf-8")
    (after_project / "change.txt").write_text("new", encoding="utf-8")
    (after_project / "add.txt").write_text("add", encoding="utf-8")

    old_snapshot, new_snapshot = tmp_path / "old.json", tmp_path / "new.json"
    create_snapshot(before_project, old_snapshot)
    create_snapshot(after_project, new_snapshot)

    assert compare_snapshots(old_snapshot, new_snapshot) == {
        "added": ["add.txt"],
        "modified": ["change.txt"],
        "deleted": ["remove.txt"],
        "unchanged": ["same.txt"],
    }


def test_compare_rejects_unsafe_snapshot_path(tmp_path: Path) -> None:
    snapshot = tmp_path / "unsafe.json"
    snapshot.write_text(
        json.dumps({"format": 1, "files": {"../outside": {"size": 0, "sha256": "0" * 64}}}),
        encoding="utf-8",
    )
    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps({"format": 1, "files": {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="unsafe"):
        compare_snapshots(valid, snapshot)


def test_compare_rejects_invalid_snapshot_metadata(tmp_path: Path) -> None:
    invalid = tmp_path / "invalid.json"
    invalid.write_text(
        json.dumps({"format": 1, "files": {"file.txt": {"size": -1, "sha256": "0" * 64}}}),
        encoding="utf-8",
    )
    valid = tmp_path / "valid.json"
    valid.write_text(json.dumps({"format": 1, "files": {}}), encoding="utf-8")

    with pytest.raises(ValueError, match="metadata"):
        compare_snapshots(valid, invalid)


def test_snapshot_excludes_its_own_output_inside_project(tmp_path: Path) -> None:
    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("print('hi')", encoding="utf-8")
    output = project / ".devaid-snapshot.json"

    create_snapshot(project, output)
    files = json.loads(output.read_text(encoding="utf-8"))["files"]
    assert ".devaid-snapshot.json" not in files
    assert "app.py" in files
