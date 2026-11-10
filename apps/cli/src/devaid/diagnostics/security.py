"""Offline security hygiene checks for local project files."""

import os
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

SKIP_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "dist",
    "build",
}
TEXT_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".json", ".toml", ".yaml", ".yml",
    ".ini", ".cfg", ".conf", ".md", ".txt", ".sh", ".ps1", ".html", ".css",
    ".env", ".properties",
}
MAX_FILE_BYTES = 1_000_000
MAX_FILES = 5_000

SECRET_PATTERNS = (
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b")),
    (
        "Credential assignment",
        re.compile(
            r"""(?i)\b(?:api[_-]?key|access[_-]?token|auth[_-]?token|client[_-]?secret|password|secret)\b\s*[:=]\s*["']?([A-Za-z0-9_./+=-]{12,})"""
        ),
    ),
)
PLACEHOLDERS = ("example", "changeme", "your_", "replace_me", "placeholder")


def _is_ignored_directory(directory: Path) -> bool:
    """Return whether a path contains a directory commonly generated or vendored."""
    return any(part in SKIP_DIRS for part in directory.parts)


def _looks_like_placeholder(value: str) -> bool:
    """Avoid reporting common documentation placeholders."""
    lowered = value.lower()
    return any(marker in lowered for marker in PLACEHOLDERS) or lowered.startswith(
        ("<", "$")
    )


def _scan_file(file_path: Path, root: Path) -> list[tuple[str, str, int, str]]:
    """Find likely exposed credentials without returning their values."""
    try:
        if file_path.stat().st_size > MAX_FILE_BYTES:
            return []
        content = file_path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return []

    findings = []
    for line_number, line in enumerate(content.splitlines(), start=1):
        for label, pattern in SECRET_PATTERNS:
            match = pattern.search(line)
            if not match:
                continue
            value = match.group(1) if match.lastindex else match.group(0)
            if label == "Credential assignment" and _looks_like_placeholder(value):
                continue
            findings.append(
                (
                    "ERROR",
                    str(file_path.relative_to(root)),
                    line_number,
                    f"Possible {label} detected; value redacted",
                )
            )
            break
    return findings



def _tracked_sensitive_files(root: Path) -> list[str]:
    """Return tracked paths that commonly contain credentials or private keys."""
    import subprocess

    try:
        result = subprocess.run(
            ["git", "-C", str(root), "ls-files", "--cached", "--"],
            capture_output=True,
            check=False,
            text=True,
            timeout=5,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    if result.returncode != 0:
        return []

    sensitive_names = {
        ".env", ".env.local", ".env.development", ".env.production",
        "id_rsa", "id_ed25519", "credentials.json", "service-account.json",
    }
    sensitive_suffixes = {".pem", ".p12", ".pfx", ".key"}
    findings = []
    for raw_path in result.stdout.splitlines():
        candidate = Path(raw_path)
        name = candidate.name.lower()
        if name in {".env.example", ".env.template", ".env.sample"}:
            continue
        if name in sensitive_names or candidate.suffix.lower() in sensitive_suffixes:
            findings.append(raw_path)
    return findings


def check_security(path: Path) -> None:
    """Check a local project for common secret-exposure risks."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    findings: list[tuple[str, str, int, str]] = []

    gitignore = root / ".gitignore"
    try:
        ignore_text = gitignore.read_text(encoding="utf-8") if gitignore.is_file() else ""
    except (OSError, UnicodeDecodeError):
        ignore_text = ""
    ignore_lines = {
        line.strip()
        for line in ignore_text.splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    protects_env = any(
        pattern in ignore_lines for pattern in (".env", ".env.*", "*.env")
    )
    findings.append(
        (
            "PASS" if protects_env else "REVIEW",
            ".gitignore",
            0,
            "Environment files are covered by an ignore rule"
            if protects_env
            else "Add .env and .env.* to .gitignore",
        )
    )

    scanned = 0
    for current, directories, filenames in os.walk(root):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        for filename in filenames:
            file_path = Path(current) / filename
            if filename == ".env":
                findings.append(
                    (
                        "ERROR",
                        str(file_path.relative_to(root)),
                        0,
                        "Environment file exists; keep it out of version control",
                    )
                )
                continue
            if filename in {".env.example", ".env.template"}:
                continue
            if file_path.suffix.lower() not in TEXT_SUFFIXES:
                continue
            scanned += 1
            if scanned > MAX_FILES:
                findings.append(
                    ("INFO", "Project scan", 0, f"Stopped after {MAX_FILES} files")
                )
                break
            findings.extend(_scan_file(file_path, root))
        if scanned > MAX_FILES:
            break

    table = Table(title=f"DevAid Security Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("File", style="cyan")
    table.add_column("Line", justify="right")
    table.add_column("Finding")
    for status, filename, line, details in findings:
        style = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}[
            status
        ]
        table.add_row(f"[{style}]{status}[/{style}]", filename, str(line or "—"), details)

    console.print(table)
    errors = sum(item[0] == "ERROR" for item in findings)
    review = sum(item[0] == "REVIEW" for item in findings)
    passed = sum(item[0] == "PASS" for item in findings)
    console.print(
        Panel(
            f"{scanned} files scanned • {passed} passed • "
            f"{review} to review • {errors} potential risks",
            title="Security hygiene summary",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Local, offline heuristic scan. Values are never printed or uploaded. "
        "This is not a complete security audit and may produce false positives.[/dim]"
    )
