"""Offline dependency manifest inspector."""

import json
import re
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

_REQUIREMENT_NAME = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)")


def _requirement_name(requirement: str) -> str | None:
    """Extract a package name from a simple PEP 508 requirement."""
    value = requirement.strip()

    if not value or value.startswith(("#", "-", "git+", "http:", "https:")):
        return None

    match = _REQUIREMENT_NAME.match(value)
    return match.group(1) if match else None


def _read_pyproject(path: Path) -> tuple[list[str], list[str]]:
    """Read PEP 621 and Poetry dependency declarations."""
    with path.open("rb") as file:
        data = tomllib.load(file)

    project = data.get("project", {})
    production = [
        name
        for item in project.get("dependencies", [])
        if (name := _requirement_name(item)) is not None
    ]

    development: list[str] = []
    optional = project.get("optional-dependencies", {})
    for requirements in optional.values():
        development.extend(
            name
            for item in requirements
            if (name := _requirement_name(item)) is not None
        )

    poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
    if not production and isinstance(poetry, dict):
        production.extend(name for name in poetry if name.lower() != "python")

    poetry_groups = data.get("tool", {}).get("poetry", {}).get("group", {})
    for group in poetry_groups.values():
        dependencies = group.get("dependencies", {})
        if isinstance(dependencies, dict):
            development.extend(dependencies)

    return production, development


def _read_requirements(path: Path) -> list[str]:
    """Read package names from a requirements file."""
    names: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        name = _requirement_name(line)
        if name is not None:
            names.append(name)
    return names


def _read_package_json(path: Path) -> tuple[list[str], list[str]]:
    """Read dependencies from a Node.js package manifest."""
    data = json.loads(path.read_text(encoding="utf-8"))
    production = list(data.get("dependencies", {}))
    development = list(data.get("devDependencies", {}))
    return production, development


def check_dependencies(path: Path) -> None:
    """Inspect dependency manifests without accessing the network."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    manifests = [
        path / "pyproject.toml",
        path / "requirements.txt",
        path / "package.json",
    ]
    found = [manifest for manifest in manifests if manifest.is_file()]

    if not found:
        console.print(
            "[yellow]No supported dependency manifests found.[/yellow]\n"
            "Supported files: pyproject.toml, requirements.txt, package.json."
        )
        return

    table = Table(title=f"DevAid Dependency Doctor — {path.resolve().name}")
    table.add_column("Manifest", style="cyan")
    table.add_column("Production", justify="right")
    table.add_column("Development", justify="right")
    table.add_column("Status", style="green")

    total_production = 0
    total_development = 0

    for manifest in found:
        try:
            if manifest.name == "pyproject.toml":
                production, development = _read_pyproject(manifest)
            elif manifest.name == "requirements.txt":
                production = _read_requirements(manifest)
                development = []
            else:
                production, development = _read_package_json(manifest)
        except (OSError, json.JSONDecodeError, tomllib.TOMLDecodeError, TypeError) as error:
            table.add_row(manifest.name, "-", "-", f"[red]Invalid: {error}[/red]")
            continue

        total_production += len(production)
        total_development += len(development)
        table.add_row(
            manifest.name,
            str(len(production)),
            str(len(development)),
            "Parsed",
        )

    console.print(table)
    console.print(
        f"\n[bold]Total declarations:[/bold] {total_production} production, "
        f"{total_development} development"
    )
    console.print(
        "[dim]Offline inspection only: this command does not check registry versions, "
        "vulnerabilities, or whether packages are outdated.[/dim]"
    )
