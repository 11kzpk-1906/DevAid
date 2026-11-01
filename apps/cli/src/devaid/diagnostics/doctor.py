"""Run the complete set of local project diagnostics."""

from pathlib import Path

import typer
from rich.console import Console
from rich.rule import Rule

from devaid.diagnostics.accessibility import accessibility_doctor
from devaid.diagnostics.config import check_config
from devaid.diagnostics.dependencies import check_dependencies
from devaid.diagnostics.deployment import check_deployment
from devaid.diagnostics.documentation import check_documentation
from devaid.diagnostics.environment import check_environment
from devaid.diagnostics.git import git_doctor
from devaid.diagnostics.health import health_check
from devaid.diagnostics.performance import performance_doctor
from devaid.diagnostics.release import release_doctor
from devaid.diagnostics.security import check_security
from devaid.diagnostics.suggestions import show_suggestions
from devaid.diagnostics.test_doctor import test_doctor

console = Console()


def run_doctor(path: Path) -> None:
    """Run all offline project checks and provide prioritized next steps."""
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
        ("Test readiness", lambda: test_doctor(root)),
        ("Git repository", lambda: git_doctor(root)),
        ("Release readiness", lambda: release_doctor(root)),
        ("Performance hygiene", lambda: performance_doctor(root)),
        ("Accessibility hygiene", lambda: accessibility_doctor(root)),
        ("Environment", check_environment),
    )

    completed = 0
    for index, (label, check) in enumerate(checks, start=1):
        console.print(Rule(f"[bold]{index}/{len(checks)} · {label}[/bold]"))
        check()
        completed += 1

    console.print(Rule("[bold cyan]Prioritized fix suggestions[/bold cyan]"))
    show_suggestions(root)

    console.print(Rule("[bold green]Full Doctor complete[/bold green]"))
    console.print(
        f"\n[bold]Final summary:[/bold] {completed}/{len(checks)} diagnostic reports "
        "completed; prioritized fix suggestions generated."
    )
    console.print(
        "[dim]Each report contains its own PASS/REVIEW/ERROR/INFO counts. "
        "Review those findings above; this summary does not combine their statuses. "
        "A clean result is not a guarantee that a project is bug-free or secure.[/dim]"
    )
