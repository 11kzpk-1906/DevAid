from collections.abc import Callable
from pathlib import Path

import typer
from rich.console import Console
from rich.rule import Rule

from devaid.diagnostics.accessibility import accessibility_doctor
from devaid.diagnostics.config import check_config
from devaid.diagnostics.dependencies import check_dependencies
from devaid.diagnostics.deployment import check_deployment
from devaid.diagnostics.docker import docker_doctor
from devaid.diagnostics.documentation import check_documentation
from devaid.diagnostics.environment import check_environment
from devaid.diagnostics.git import git_doctor
from devaid.diagnostics.health import health_check
from devaid.diagnostics.javascript import javascript_doctor
from devaid.diagnostics.package_manager import package_doctor
from devaid.diagnostics.performance import performance_doctor
from devaid.diagnostics.python_project import python_doctor
from devaid.diagnostics.release import release_doctor
from devaid.diagnostics.security import check_security
from devaid.diagnostics.security_code import check_security_code
from devaid.diagnostics.suggestions import show_suggestions
from devaid.diagnostics.tests_readiness import test_doctor
from devaid.diagnostics.workflows import workflow_doctor
from devaid.settings import load_skipped_checks

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

    checks: tuple[tuple[str, str, Callable[[], None]], ...] = (
        ("health", "Project health", lambda: health_check(root)),
        ("dependencies", "Dependencies", lambda: check_dependencies(root)),
        ("configuration", "Configuration", lambda: check_config(root)),
        ("deployment", "Deployment", lambda: check_deployment(root)),
        ("documentation", "Documentation", lambda: check_documentation(root)),
        ("security", "Security hygiene", lambda: check_security(root)),
        ("security-code", "Static code security", lambda: check_security_code(root)),
        ("tests", "Test readiness", lambda: test_doctor(root)),
        ("git", "Git repository", lambda: git_doctor(root)),
        ("release", "Release readiness", lambda: release_doctor(root)),
        ("performance", "Performance hygiene", lambda: performance_doctor(root)),
        ("accessibility", "Accessibility hygiene", lambda: accessibility_doctor(root)),
        ("workflows", "GitHub Actions workflows", lambda: workflow_doctor(root)),
        ("docker", "Docker configuration", lambda: docker_doctor(root)),
        ("packages", "Package manager consistency", lambda: package_doctor(root)),
        ("python", "Python project conventions", lambda: python_doctor(root)),
        ("javascript", "JavaScript project conventions", lambda: javascript_doctor(root)),
        ("environment", "Environment", check_environment),
    )

    try:
        skipped = load_skipped_checks(root)
    except ValueError as error:
        console.print(f"[bold red]Invalid DevAid configuration:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    active_checks = [item for item in checks if item[0] not in skipped]
    skipped_count = len(checks) - len(active_checks)
    if skipped_count:
        console.print(
            f"[yellow]Skipping {skipped_count} diagnostic(s) from "
            ".devaid.toml.[/yellow]"
        )

    completed = 0
    for index, (_, label, check) in enumerate(active_checks, start=1):
        console.print(Rule(f"[bold]{index}/{len(active_checks)} · {label}[/bold]"))
        check()  # All registered diagnostics are normalized to a no-argument callable.
        completed += 1

    console.print(Rule("[bold cyan]Prioritized fix suggestions[/bold cyan]"))
    show_suggestions(root)

    console.print(Rule("[bold green]Full Doctor complete[/bold green]"))
    console.print(
        f"\n[bold]Final summary:[/bold] {completed}/{len(active_checks)} diagnostic reports "
        "completed; prioritized fix suggestions generated."
    )
    console.print(
        "[dim]Each report contains its own PASS/REVIEW/ERROR/INFO counts. "
        "Review those findings above; this summary does not combine their statuses. "
        "A clean result is not a guarantee that a project is bug-free or secure.[/dim]"
    )
