"""Offline release-readiness diagnostics."""

import json
import re
import subprocess
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _read_version(path: Path, kind: str) -> str | None:
    """Read a project version from a supported manifest."""
    try:
        if kind == "python":
            data = tomllib.loads(path.read_text(encoding="utf-8"))
            value = data.get("project", {}).get("version")
        else:
            data = json.loads(path.read_text(encoding="utf-8"))
            value = data.get("version")
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, tomllib.TOMLDecodeError):
        return None
    return value if isinstance(value, str) and value.strip() else None


def inspect_release(path: Path) -> list[tuple[str, str, str]]:
    """Return local release-readiness findings without changing project files."""
    findings: list[tuple[str, str, str]] = []
    pyproject = path / "pyproject.toml"
    package_json = path / "package.json"
    versions: list[tuple[str, str]] = []

    for manifest, kind, label in (
        (pyproject, "python", "pyproject.toml"),
        (package_json, "node", "package.json"),
    ):
        if manifest.is_file():
            version = _read_version(manifest, kind)
            if version:
                versions.append((label, version))
                findings.append(("Version metadata", "PASS", f"{label}: {version}"))
            else:
                findings.append(("Version metadata", "ERROR", f"{label} has no valid version"))

    if not versions:
        findings.append(("Version metadata", "REVIEW", "No supported project version found"))
    elif len({version for _, version in versions}) > 1:
        findings.append(
            ("Version consistency", "REVIEW", "Version values differ across manifests")
        )
    elif len(versions) > 1:
        findings.append(("Version consistency", "PASS", "Manifest versions match"))

    changelog = path / "CHANGELOG.md"
    if not changelog.is_file():
        findings.append(("Changelog", "REVIEW", "CHANGELOG.md is missing"))
    else:
        try:
            content = changelog.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(("Changelog", "ERROR", "CHANGELOG.md could not be read as UTF-8"))
        else:
            has_release_entry = bool(
                re.search(r"^##?\s+\[?\d+\.\d+\.\d+", content, re.MULTILINE)
            )
            findings.append(
                (
                    "Changelog",
                    "PASS" if has_release_entry else "REVIEW",
                    "A versioned release heading was found"
                    if has_release_entry
                    else "Add a versioned release heading (for example, 1.0.0)",
                )
            )

    license_file = next(
        (
            path / name
            for name in ("LICENSE", "LICENSE.md", "LICENSE.txt")
            if (path / name).is_file()
        ),
        None,
    )
    findings.append(
        (
            "License",
            "PASS" if license_file else "REVIEW",
            f"{license_file.name} found" if license_file else "No license file found",
        )
    )

    package_markers = (
        (path / "pyproject.toml").is_file(),
        (path / "package.json").is_file(),
        (path / "Cargo.toml").is_file(),
        (path / "go.mod").is_file(),
    )
    findings.append(
        (
            "Packaging metadata",
            "PASS" if any(package_markers) else "REVIEW",
            "A supported package manifest was found"
            if any(package_markers)
            else "No common package manifest found",
        )
    )

    try:
        tags = subprocess.run(
            ["git", "tag", "--list"],
            cwd=path,
            capture_output=True,
            text=True,
            check=False,
            timeout=5,
        )
    except (FileNotFoundError, subprocess.TimeoutExpired):
        tags = None

    if tags is None or tags.returncode != 0:
        findings.append(("Git release tags", "INFO", "Git tags could not be inspected"))
    elif tags.stdout.strip():
        tag_lines = [tag for tag in tags.stdout.splitlines() if tag.strip()]
        findings.append(
            ("Git release tags", "PASS", f"{len(tag_lines)} tag(s) found")
        )
    else:
        findings.append(("Git release tags", "REVIEW", "No Git tags found yet"))

    workflows = path / ".github" / "workflows"
    release_workflow = workflows.is_dir() and any(
        re.search(r"release|publish|deploy", item.stem, re.IGNORECASE)
        for item in workflows.glob("*.y*ml")
    )
    findings.append(
        (
            "Release workflow",
            "PASS" if release_workflow else "INFO",
            "A release, publish, or deploy workflow file was found"
            if release_workflow
            else "No obvious release workflow found (optional)",
        )
    )
    return findings


def release_doctor(path: Path) -> None:
    """Display an offline release-readiness report."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings = inspect_release(path)
    table = Table(title=f"DevAid Release Doctor — {path.resolve().name}")
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
        "[dim]Offline readiness checks only. DevAid does not create releases, "
        "publish packages, modify tags, or contact hosting services.[/dim]"
    )
