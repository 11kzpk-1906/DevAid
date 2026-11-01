"""Read-only project performance hygiene diagnostics."""

import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", ".next", ".nuxt",
    "coverage", "target",
}
SOURCE_SUFFIXES = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".go", ".rs", ".java", ".css",
    ".scss", ".html",
}
MAX_FILES = 5000
MAX_FILE_BYTES = 10 * 1024 * 1024


def inspect_performance(path: Path) -> list[tuple[str, str, str]]:
    """Return static performance hygiene findings without running project code."""
    findings: list[tuple[str, str, str]] = []
    package_json = path / "package.json"

    if package_json.is_file():
        try:
            package = json.loads(package_json.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            findings.append(("Node build setup", "ERROR", "package.json is not valid readable JSON"))
        else:
            scripts = package.get("scripts", {})
            if isinstance(scripts, dict) and any(
                key in scripts for key in ("build", "bundle", "compile")
            ):
                findings.append(("Node build setup", "PASS", "A build script is defined"))
            else:
                findings.append(("Node build setup", "REVIEW", "No build script was found"))

            if (path / "pnpm-lock.yaml").is_file() or (path / "package-lock.json").is_file() or (
                path / "yarn.lock"
            ).is_file() or (path / "bun.lockb").is_file() or (path / "bun.lock").is_file():
                findings.append(("Dependency reproducibility", "PASS", "A Node lockfile was found"))
            else:
                findings.append(
                    ("Dependency reproducibility", "REVIEW", "No Node lockfile was found")
                )

    if (path / "pyproject.toml").is_file() or (path / "requirements.txt").is_file():
        if (path / "uv.lock").is_file() or (path / "poetry.lock").is_file() or (
            path / "Pipfile.lock"
        ).is_file():
            findings.append(("Python dependency reproducibility", "PASS", "A Python lockfile was found"))
        else:
            findings.append(
                ("Python dependency reproducibility", "INFO", "No supported Python lockfile found")
            )

    ignore_file = path / ".gitignore"
    if ignore_file.is_file():
        try:
            ignore_text = ignore_file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(("Generated files", "REVIEW", ".gitignore could not be read"))
        else:
            patterns = (".venv", "venv", "__pycache__", "node_modules", "dist", "build")
            missing = [item for item in patterns if item not in ignore_text]
            findings.append(
                (
                    "Generated files",
                    "PASS" if not missing else "REVIEW",
                    "Common generated folders are ignored"
                    if not missing
                    else "Consider ignoring: " + ", ".join(missing),
                )
            )
    else:
        findings.append(("Generated files", "REVIEW", ".gitignore is missing"))

    scanned = 0
    large_sources: list[str] = []
    large_assets: list[str] = []
    truncated = False

    for current, directories, files in os.walk(path):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        for filename in files:
            scanned += 1
            if scanned > MAX_FILES:
                truncated = True
                break
            item = Path(current) / filename
            try:
                size = item.stat().st_size
            except OSError:
                continue
            relative = item.relative_to(path).as_posix()
            if size > MAX_FILE_BYTES:
                if item.suffix.lower() in SOURCE_SUFFIXES:
                    large_sources.append(relative)
                elif size > 25 * 1024 * 1024:
                    large_assets.append(relative)
        if truncated:
            break

    if large_sources:
        findings.append(
            (
                "Large source files",
                "REVIEW",
                f"{len(large_sources)} source file(s) exceed 10 MB; consider splitting them",
            )
        )
    else:
        findings.append(("Large source files", "PASS", "No source files above 10 MB were found"))

    if large_assets:
        findings.append(
            (
                "Large assets",
                "REVIEW",
                f"{len(large_assets)} asset file(s) exceed 25 MB; consider compression or external storage",
            )
        )
    else:
        findings.append(("Large assets", "PASS", "No files above 25 MB were found"))

    findings.append(
        (
            "Scan coverage",
            "INFO" if truncated else "PASS",
            f"Inspected metadata for {min(scanned, MAX_FILES)} file(s)"
            + ("; scan stopped at the 5,000-file safety limit" if truncated else ""),
        )
    )
    return findings


def performance_doctor(path: Path) -> None:
    """Display read-only performance hygiene findings."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings = inspect_performance(path)
    table = Table(title=f"DevAid Performance Doctor — {path.resolve().name}")
    table.add_column("Area", style="cyan")
    table.add_column("Status")
    table.add_column("Details")
    styles = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}
    for area, status, details in findings:
        table.add_row(area, f"[{styles[status]}]{status}[/{styles[status]}]", details)
    console.print(table)

    passed = sum(status == "PASS" for _, status, _ in findings)
    review = sum(status == "REVIEW" for _, status, _ in findings)
    errors = sum(status == "ERROR" for _, status, _ in findings)
    info = sum(status == "INFO" for _, status, _ in findings)
    console.print(
        f"\n[bold]Final summary:[/bold] {passed} passed • {review} to review • "
        f"{errors} errors • {info} informational"
    )
    console.print(
        "[dim]Static checks only. DevAid does not benchmark, execute, install, "
        "or modify project code. Findings are suggestions, not measured bottlenecks.[/dim]"
    )
