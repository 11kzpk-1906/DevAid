"""Offline configuration hygiene checks."""

import json
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _validate_json(path: Path) -> str | None:
    """Return a validation error for a JSON file, if any."""
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return str(error)
    return None


def _validate_toml(path: Path) -> str | None:
    """Return a validation error for a TOML file, if any."""
    try:
        with path.open("rb") as file:
            tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return str(error)
    return None


def check_config(path: Path) -> None:
    """Check common project configuration files without reading secret values."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings: list[tuple[str, str, str]] = []

    gitignore = path / ".gitignore"
    if gitignore.is_file():
        try:
            entries = {
                line.strip()
                for line in gitignore.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
            missing = [
                pattern
                for pattern in (".env", ".venv/", "__pycache__/", "node_modules/")
                if pattern not in entries
            ]
            if missing:
                findings.append(
                    (".gitignore", "REVIEW", "Consider ignoring: " + ", ".join(missing))
                )
            else:
                findings.append((".gitignore", "PASS", "Common local files are ignored"))
        except (OSError, UnicodeDecodeError) as error:
            findings.append((".gitignore", "ERROR", str(error)))
    else:
        findings.append((".gitignore", "REVIEW", "No .gitignore file found"))

    editorconfig = path / ".editorconfig"
    if editorconfig.is_file():
        try:
            text = editorconfig.read_text(encoding="utf-8")
            if "root = true" in text and "[*]" in text:
                findings.append((".editorconfig", "PASS", "Root and global rules found"))
            else:
                findings.append(
                    (".editorconfig", "REVIEW", "Add root = true and a [*] section")
                )
        except (OSError, UnicodeDecodeError) as error:
            findings.append((".editorconfig", "ERROR", str(error)))
    else:
        findings.append((".editorconfig", "REVIEW", "No .editorconfig file found"))

    for filename, validator in (
        ("pyproject.toml", _validate_toml),
        ("package.json", _validate_json),
    ):
        config_file = path / filename
        if config_file.is_file():
            error = validator(config_file)
            if error is None:
                findings.append((filename, "PASS", "Syntax is valid"))
            else:
                findings.append((filename, "ERROR", error))

    if (path / ".env").is_file():
        if (path / ".env.example").is_file():
            findings.append((".env.example", "PASS", "Example template found"))
        else:
            findings.append(
                (".env.example", "REVIEW", "Add a template without real secret values")
            )

    table = Table(title=f"DevAid Config Doctor — {path.resolve().name}")
    table.add_column("Configuration", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for filename, status, details in findings:
        style = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red"}[status]
        table.add_row(filename, f"[{style}]{status}[/{style}]", details)

    console.print(table)
    passed = sum(status == "PASS" for _, status, _ in findings)
    review = sum(status == "REVIEW" for _, status, _ in findings)
    errors = sum(status == "ERROR" for _, status, _ in findings)
    console.print(
        f"\n[bold]Summary:[/bold] {passed} passed • {review} to review • {errors} errors"
    )
    console.print(
        "[dim]Offline checks only. DevAid never reads .env contents or transmits "
        "configuration values.[/dim]"
    )
