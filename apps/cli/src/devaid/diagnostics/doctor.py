"""Run the complete set of local project diagnostics."""

from pathlib import Path

import typer
from rich.console import Console
from rich.rule import Rule

from devaid.diagnostics.config import check_config
from devaid.diagnostics.dependencies import check_dependencies
from devaid.diagnostics.deployment import check_deployment
from devaid.diagnostics.documentation import check_documentation
from devaid.diagnostics.environment import check_environment
from devaid.diagnostics.health import health_check
from devaid.diagnostics.security import check_security

console = Console()


def run_doctor(path: Path) -> None:
    """Run all offline project checks in one command."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    console.print(Rule(f"[bold cyan]DevAid Full Doctor — {root.name}[/bold cyan]"))
    console.print(
        "[dim]Running local diagnostics. Checks are read-only; no files are changed "
        "and no project source is uploaded.[/dim]\n"
    )

    checks = (
        ("Project health", lambda: health_check(root)),
        ("Dependencies", lambda: check_dependencies(root)),
        ("Configuration", lambda: check_config(root)),
        ("Deployment", lambda: check_deployment(root)),
        ("Documentation", lambda: check_documentation(root)),
        ("Security hygiene", lambda: check_security(root)),
        ("Environment", check_environment),
    )

    for index, (label, check) in enumerate(checks, start=1):
        console.print(Rule(f"[bold]{index}/{len(checks)} · {label}[/bold]"))
        check()

    console.print(
        Rule("[bold green]Full Doctor complete[/bold green]")
    )
    console.print(
        "[dim]Review each report above. A clean result is a useful baseline, "
        "not a guarantee that a project is bug-free or secure.[/dim]"
    )
