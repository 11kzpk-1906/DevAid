"""Offline deployment configuration diagnostics."""

import json
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


def _validate_json(path: Path) -> str | None:
    """Return a JSON syntax error, if one exists."""
    try:
        json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as error:
        return str(error)
    return None


def _validate_toml(path: Path) -> str | None:
    """Return a TOML syntax error, if one exists."""
    try:
        with path.open("rb") as file:
            tomllib.load(file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        return str(error)
    return None


def check_deployment(path: Path) -> None:
    """Inspect common deployment files without contacting hosting providers."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings: list[tuple[str, str, str]] = []
    configs = (
        ("vercel.json", _validate_json),
        ("netlify.toml", _validate_toml),
    )
    detected: list[str] = []

    for filename, validator in configs:
        config_path = path / filename
        if config_path.is_file():
            detected.append(filename)
            error = validator(config_path)
            findings.append(
                (
                    filename,
                    "ERROR" if error else "PASS",
                    f"Invalid syntax: {error}" if error else "Syntax is valid",
                )
            )

    render = path / "render.yaml"
    if render.is_file():
        detected.append("render.yaml")
        try:
            text = render.read_text(encoding="utf-8")
            has_service = "services:" in text
            findings.append(
                (
                    "render.yaml",
                    "PASS" if has_service else "REVIEW",
                    "Services section found"
                    if has_service
                    else "Check that the blueprint defines services",
                )
            )
        except (OSError, UnicodeDecodeError) as error:
            findings.append(("render.yaml", "ERROR", str(error)))

    dockerfile = path / "Dockerfile"
    if dockerfile.is_file():
        detected.append("Dockerfile")
        try:
            lines = [
                line.strip()
                for line in dockerfile.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            has_runtime = any(
                line.upper().startswith(("CMD ", "ENTRYPOINT ")) for line in lines
            )
            findings.append(
                (
                    "Dockerfile runtime",
                    "PASS" if has_runtime else "REVIEW",
                    "CMD or ENTRYPOINT found"
                    if has_runtime
                    else "Consider defining CMD or ENTRYPOINT",
                )
            )
        except (OSError, UnicodeDecodeError) as error:
            findings.append(("Dockerfile", "ERROR", str(error)))

    procfile = path / "Procfile"
    if procfile.is_file():
        detected.append("Procfile")
        try:
            has_web = any(
                line.strip().startswith("web: ")
                for line in procfile.read_text(encoding="utf-8").splitlines()
            )
            findings.append(
                (
                    "Procfile web process",
                    "PASS" if has_web else "REVIEW",
                    "web process found"
                    if has_web
                    else "No web: process declaration found",
                )
            )
        except (OSError, UnicodeDecodeError) as error:
            findings.append(("Procfile", "ERROR", str(error)))

    compose_files = ("compose.yaml", "compose.yml", "docker-compose.yml")
    compose_found = [name for name in compose_files if (path / name).is_file()]
    if compose_found:
        detected.extend(compose_found)
        findings.append(
            (
                "Container Compose",
                "INFO",
                "Found " + ", ".join(compose_found) + "; review service and port settings",
            )
        )

    if not detected:
        findings.append(
            (
                "Deployment configuration",
                "INFO",
                "No supported deployment files detected",
            )
        )

    table = Table(title=f"DevAid Deployment Doctor — {path.resolve().name}")
    table.add_column("Configuration", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for label, status, details in findings:
        style = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}[
            status
        ]
        table.add_row(label, f"[{style}]{status}[/{style}]", details)

    console.print(table)
    passed = sum(status == "PASS" for _, status, _ in findings)
    review = sum(status == "REVIEW" for _, status, _ in findings)
    errors = sum(status == "ERROR" for _, status, _ in findings)
    console.print(
        Panel(
            f"{passed} passed • {review} to review • {errors} errors",
            title="Deployment configuration summary",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Offline configuration checks only. DevAid does not deploy, contact "
        "hosting providers, execute commands, or inspect secret values.[/dim]"
    )
