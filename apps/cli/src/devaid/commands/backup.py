"""Create, verify, and safely restore local project archives."""

from __future__ import annotations

import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath
from typing import Any

MANIFEST_NAME = "__devaid_backup__.json"
EXCLUDED_DIRECTORIES = {
    ".git", ".hg", ".svn", ".venv", "venv", "env", "node_modules",
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    ".tox", ".nox", ".next", ".nuxt", "dist", "build",
}
EXCLUDED_FILE_NAMES = {
    ".env", ".env.local", ".env.development", ".env.production",
    "id_rsa", "id_ed25519", "credentials.json",
}
EXCLUDED_SUFFIXES = {".pem", ".key", ".p12", ".pfx"}


def _is_sensitive_file(path: Path) -> bool:
    name = path.name.lower()
    if name in EXCLUDED_FILE_NAMES or path.suffix.lower() in EXCLUDED_SUFFIXES:
        return True
    return name.startswith(".env.") and name not in {".env.example", ".env.sample"}


def _safe_archive_path(name: str) -> PurePosixPath:
    if not name or "\\" in name:
        raise ValueError("The backup contains an unsafe file path.")
    path = PurePosixPath(name)
    if path.is_absolute() or any(part in {"", ".", ".."} for part in path.parts):
        raise ValueError("The backup contains an unsafe file path.")
    return path


def _sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def backup_project(source: Path, output: Path | None = None) -> Path:
    """Create a ZIP backup, excluding caches, VCS data, and common secrets."""
    source = source.expanduser().resolve()
    if not source.is_dir():
        raise ValueError(f"Project directory does not exist: {source}")

    if output is None:
        output = source.parent / f"{source.name}-backup.zip"
    output = output.expanduser().resolve()
    if output.exists():
        raise FileExistsError(f"Backup already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)

    files: list[tuple[str, Path]] = []
    for root, directories, filenames in os.walk(source, followlinks=False):
        root_path = Path(root)
        directories[:] = [
            name for name in directories
            if name not in EXCLUDED_DIRECTORIES
            and not (root_path / name).is_symlink()
        ]
        for filename in filenames:
            file_path = root_path / filename
            if file_path.is_symlink() or _is_sensitive_file(file_path):
                continue
            if file_path.resolve() == output:
                continue
            relative = file_path.relative_to(source).as_posix()
            files.append((relative, file_path))

    manifest: list[dict[str, Any]] = []
    try:
        with zipfile.ZipFile(output, "w", compression=zipfile.ZIP_DEFLATED) as archive:
            for relative, file_path in sorted(files):
                data = file_path.read_bytes()
                archive.writestr(relative, data)
                manifest.append({
                    "path": relative,
                    "size": len(data),
                    "sha256": _sha256(data),
                })
            archive.writestr(
                MANIFEST_NAME,
                json.dumps({"format": 1, "files": manifest}, indent=2) + "\n",
            )
    except OSError:
        output.unlink(missing_ok=True)
        raise
    return output


def verify_backup(archive_path: Path) -> int:
    """Validate archive paths and every file's recorded size and SHA-256."""
    with zipfile.ZipFile(archive_path, "r") as archive:
        infos = archive.infolist()
        names = [info.filename for info in infos]
        if len(names) != len(set(names)):
            raise ValueError("The backup contains duplicate archive entries.")
        if MANIFEST_NAME not in names:
            raise ValueError("The backup manifest is missing.")

        for info in infos:
            if info.filename != MANIFEST_NAME:
                _safe_archive_path(info.filename)
            mode = info.external_attr >> 16
            if stat.S_ISLNK(mode):
                raise ValueError("The backup contains a symbolic link.")

        try:
            manifest = json.loads(archive.read(MANIFEST_NAME))
        except (json.JSONDecodeError, UnicodeDecodeError) as error:
            raise ValueError("The backup manifest is invalid.") from error

        if not isinstance(manifest, dict) or manifest.get("format") != 1:
            raise ValueError("Unsupported backup format.")
        entries = manifest.get("files")
        if not isinstance(entries, list):
            raise ValueError("The backup manifest has no valid file list.")

        expected: set[str] = set()
        for entry in entries:
            if not isinstance(entry, dict):
                raise ValueError("The backup manifest contains an invalid entry.")
            name = entry.get("path")
            if not isinstance(name, str):
                raise ValueError("The backup manifest contains an invalid path.")
            _safe_archive_path(name)
            if name == MANIFEST_NAME or name in expected:
                raise ValueError("The backup manifest contains a duplicate path.")
            expected.add(name)
            try:
                data = archive.read(name)
            except KeyError as error:
                raise ValueError(f"Backup file is missing: {name}") from error
            if entry.get("size") != len(data) or entry.get("sha256") != _sha256(data):
                raise ValueError(f"Backup integrity check failed: {name}")

        actual = set(names) - {MANIFEST_NAME}
        if actual != expected:
            raise ValueError("The archive contents do not match its manifest.")
        return len(entries)


def restore_backup(archive_path: Path, destination: Path) -> int:
    """Restore into a new directory; never overwrite an existing destination."""
    archive_path = archive_path.expanduser().resolve()
    destination = destination.expanduser().resolve()
    if destination.exists():
        raise FileExistsError(f"Restore destination already exists: {destination}")
    if not destination.parent.is_dir():
        raise FileNotFoundError(f"Destination parent does not exist: {destination.parent}")

    file_count = verify_backup(archive_path)
    with tempfile.TemporaryDirectory(
        prefix=".devaid-restore-",
        dir=destination.parent,
    ) as temporary:
        staging = Path(temporary) / "project"
        staging.mkdir()
        with zipfile.ZipFile(archive_path, "r") as archive:
            for info in archive.infolist():
                if info.filename == MANIFEST_NAME:
                    continue
                relative = _safe_archive_path(info.filename)
                target = staging.joinpath(*relative.parts)
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_bytes(archive.read(info.filename))
        os.replace(staging, destination)
    return file_count
