"""Create and compare deterministic local project snapshots."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
from typing import Any

SNAPSHOT_FORMAT = 1
EXCLUDED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", ".next", ".nuxt", "dist", "build",
}
EXCLUDED_FILES = {
    ".env", ".env.local", ".env.development", ".env.production",
    "id_rsa", "id_ed25519", "credentials.json",
}
EXCLUDED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def _is_sensitive(path: Path) -> bool:
    name = path.name.lower()
    if name in EXCLUDED_FILES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return name.startswith(".env.") and name not in {".env.example", ".env.sample"}


def _safe_relative_path(value: str) -> PurePosixPath:
    if not value or "\\" in value:
        raise ValueError("Snapshot contains an unsafe file path.")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or PureWindowsPath(value).drive
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise ValueError("Snapshot contains an unsafe file path.")
    return path


def _digest(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def create_snapshot(source: Path, output: Path) -> Path:
    """Write a JSON snapshot of relative file paths, sizes, and SHA-256 hashes."""
    source = source.expanduser().resolve()
    output = output.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"Project directory does not exist: {source}")
    if output.exists():
        raise FileExistsError(f"Snapshot already exists: {output}")

    files: dict[str, dict[str, Any]] = {}
    for root, directories, filenames in os.walk(source, followlinks=False):
        root_path = Path(root)
        directories[:] = [
            name for name in directories
            if name not in EXCLUDED_DIRECTORIES
            and not (root_path / name).is_symlink()
        ]
        for filename in filenames:
            file_path = root_path / filename
            if file_path.is_symlink() or _is_sensitive(file_path):
                continue
            if file_path.resolve() == output:
                continue
            relative = file_path.relative_to(source).as_posix()
            _safe_relative_path(relative)
            stat = file_path.stat()
            files[relative] = {"size": stat.st_size, "sha256": _digest(file_path)}

    payload = {"format": SNAPSHOT_FORMAT, "files": dict(sorted(files.items()))}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return output


def _load_snapshot(path: Path) -> dict[str, dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as error:
        raise ValueError(f"Could not read snapshot: {path}") from error
    if not isinstance(payload, dict) or payload.get("format") != SNAPSHOT_FORMAT:
        raise ValueError("Unsupported or invalid snapshot format.")
    files = payload.get("files")
    if not isinstance(files, dict):
        raise ValueError("Snapshot file list is invalid.")

    validated: dict[str, dict[str, Any]] = {}
    for name, metadata in files.items():
        if not isinstance(name, str):
            raise ValueError("Snapshot contains an invalid path.")
        _safe_relative_path(name)
        if not isinstance(metadata, dict):
            raise ValueError(f"Invalid metadata for snapshot file: {name}")
        size = metadata.get("size")
        digest = metadata.get("sha256")
        if (
            not isinstance(size, int)
            or isinstance(size, bool)
            or size < 0
            or not isinstance(digest, str)
            or len(digest) != 64
            or any(character not in "0123456789abcdef" for character in digest)
        ):
            raise ValueError(f"Invalid metadata for snapshot file: {name}")
        validated[name] = {"size": size, "sha256": digest}
    return validated


def compare_snapshots(before: Path, after: Path) -> dict[str, list[str]]:
    """Classify paths as added, modified, deleted, or unchanged."""
    old = _load_snapshot(before)
    new = _load_snapshot(after)
    old_names, new_names = set(old), set(new)
    added = new_names - old_names
    deleted = old_names - new_names
    common = old_names & new_names
    modified = {name for name in common if old[name] != new[name]}
    unchanged = common - modified
    return {
        "added": sorted(added),
        "modified": sorted(modified),
        "deleted": sorted(deleted),
        "unchanged": sorted(unchanged),
    }
