"""DevAid CLI entry point."""

import zipfile
from pathlib import Path

import typer
from rich.console import Console
from rich.prompt import Prompt

from devaid import __version__
from devaid.analyzers.project import analyze_project
from devaid.commands.backup import backup_project, restore_backup, verify_backup
from devaid.commands.explain import explain
from devaid.commands.snapshot import compare_snapshots, create_snapshot
from devaid.commands.update_checker import update_check
from devaid.diagnostics.accessibility import accessibility_doctor
from devaid.diagnostics.api import inspect_api
from devaid.diagnostics.config import check_config
from devaid.diagnostics.dependencies import check_dependencies
from devaid.diagnostics.deployment import check_deployment
from devaid.diagnostics.docker import docker_doctor
from devaid.diagnostics.doctor import run_doctor
from devaid.diagnostics.documentation import check_documentation
from devaid.diagnostics.environment import check_environment
from devaid.diagnostics.git import git_doctor
from devaid.diagnostics.health import health_check
from devaid.diagnostics.javascript import javascript_doctor
from devaid.diagnostics.package_manager import package_doctor
from devaid.diagnostics.performance import performance_doctor
from devaid.diagnostics.python_project import python_doctor
from devaid.diagnostics.release import release_doctor
from devaid.diagnostics.reports import report
from devaid.diagnostics.security import check_security
from devaid.diagnostics.security_code import check_security_code
from devaid.diagnostics.suggestions import show_suggestions
from devaid.diagnostics.test_doctor import test_doctor
from devaid.diagnostics.workflows import workflow_doctor
from devaid.plugins import discover_analyzer_plugins, run_analyzer_plugin
from devaid.settings import create_default_config

app = typer.Typer(
    name="devaid",
    help="An open-source toolkit for developers.",
    no_args_is_help=True,
)

console = Console()
BACKUP_OUTPUT_OPTION = typer.Option(None, "--output", "-o")
BACKUP_VERIFY_ARCHIVE_ARGUMENT = typer.Argument(...)
RESTORE_ARCHIVE_ARGUMENT = typer.Argument(...)
RESTORE_DESTINATION_OPTION = typer.Option(..., "--destination", "-d")
SNAPSHOT_OUTPUT_OPTION = typer.Option(None, "--output", "-o")
SNAPSHOT_BEFORE_ARGUMENT = typer.Argument(...)
SNAPSHOT_AFTER_ARGUMENT = typer.Argument(...)


@app.callback()
def main() -> None:
    """Build better. Debug smarter. Ship confidently."""


@app.command()
def version() -> None:
    """Display the DevAid version."""
    console.print(f"[bold cyan]DevAid[/bold cyan] v{__version__}")


app.command(name="explain")(explain)
app.command(name="update-check")(update_check)
app.command(name="analyze")(analyze_project)
app.command(name="deps")(check_dependencies)
app.command(name="doctor")(run_doctor)
app.command(name="suggest")(show_suggestions)
app.command(name="test-doctor")(test_doctor)
app.command(name="git")(git_doctor)
app.command(name="release")(release_doctor)
app.command(name="performance")(performance_doctor)
app.command(name="accessibility")(accessibility_doctor)
app.command(name="deploy")(check_deployment)
app.command(name="health")(health_check)
app.command(name="config")(check_config)
app.command(name="env")(check_environment)
app.command(name="api")(inspect_api)
app.command(name="docs")(check_documentation)
app.command(name="security")(check_security)
app.command(name="security-code")(check_security_code)
app.command(name="workflow-doctor")(workflow_doctor)
app.command(name="docker-doctor")(docker_doctor)
app.command(name="package-doctor")(package_doctor)
app.command(name="python-doctor")(python_doctor)
app.command(name="javascript-doctor")(javascript_doctor)
app.command(name="report")(report)


@app.command()
def welcome(path: Path = Path(".")) -> None:
    """Show a guided first-run menu for common DevAid tasks."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    console.print("[bold cyan]Welcome to DevAid![/bold cyan]")
    console.print("Build better. Debug smarter. Ship confidently.")
    console.print(f"\nProject: [cyan]{path.resolve()}[/cyan]")
    console.print("Choose what you would like to do first.")

    choices = ["doctor", "analyze", "dashboard", "config", "help", "quit"]
    choice = Prompt.ask("Getting started", choices=choices, default="doctor")

    if choice == "doctor":
        run_doctor(path)
    elif choice == "analyze":
        analyze_project(path)
    elif choice == "dashboard":
        dashboard(path)
    elif choice == "config":
        config_init(path)
    elif choice == "help":
        console.print("Run `devaid --help` to explore every available command.")
    else:
        console.print("Welcome menu closed. Happy building!")


@app.command(name="backup")
def backup_command(
    path: Path = Path("."),
    output: Path | None = BACKUP_OUTPUT_OPTION,
) -> None:
    """Create a local ZIP backup of a project, excluding common secrets and caches."""
    try:
        archive_path = backup_project(path, output)
    except (OSError, ValueError) as error:
        console.print(f"[bold red]Backup failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Backup created:[/green] {archive_path}")


@app.command(name="backup-verify")
def backup_verify_command(archive: Path = BACKUP_VERIFY_ARCHIVE_ARGUMENT) -> None:
    """Verify a DevAid backup manifest and every archived file checksum."""
    try:
        file_count = verify_backup(archive)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        console.print(f"[bold red]Backup verification failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Backup verified.[/green] {file_count} files passed integrity checks.")


@app.command(name="restore")
def restore_command(
    archive: Path = RESTORE_ARCHIVE_ARGUMENT,
    destination: Path = RESTORE_DESTINATION_OPTION,
) -> None:
    """Restore a verified backup into a new directory without overwriting files."""
    try:
        file_count = restore_backup(archive, destination)
    except (OSError, ValueError, zipfile.BadZipFile) as error:
        console.print(f"[bold red]Restore failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Restored {file_count} files to {destination.resolve()}[/green]")



@app.command(name="snapshot")
def snapshot_command(
    path: Path = Path("."),
    output: Path | None = SNAPSHOT_OUTPUT_OPTION,
) -> None:
    """Capture a local project snapshot with file sizes and SHA-256 hashes."""
    target = output if output is not None else path / ".devaid-snapshot.json"
    try:
        snapshot_path = create_snapshot(path, target)
    except (OSError, ValueError) as error:
        console.print(f"[bold red]Snapshot failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Snapshot created:[/green] {snapshot_path}")


@app.command(name="snapshot-compare")
def snapshot_compare_command(
    before: Path = SNAPSHOT_BEFORE_ARGUMENT,
    after: Path = SNAPSHOT_AFTER_ARGUMENT,
) -> None:
    """Compare two snapshots and list added, modified, and deleted files."""
    try:
        changes = compare_snapshots(before, after)
    except (OSError, ValueError) as error:
        console.print(f"[bold red]Snapshot comparison failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

    for category in ("added", "modified", "deleted", "unchanged"):
        paths = changes[category]
        console.print(f"\n[bold cyan]{category.title()} ({len(paths)})[/bold cyan]")
        for item in paths:
            console.print(f"  {item}")
    console.print(
        "\n[bold]Summary:[/bold] "
        + ", ".join(f"{name}: {len(paths)}" for name, paths in changes.items())
    )

@app.command(name="config-init")
def config_init(path: Path = Path(".")) -> None:
    """Create a starter .devaid.toml diagnostic profile."""
    try:
        config_path = create_default_config(path)
    except (FileExistsError, NotADirectoryError, OSError) as error:
        console.print(f"[bold red]Could not create config:[/bold red] {error}")
        raise typer.Exit(code=1) from error
    console.print(f"[green]Created {config_path}[/green]")
    console.print("Edit [doctor].skip to disable selected full-doctor checks.")


@app.command()
def dashboard(path: Path = Path(".")) -> None:
    """Open an interactive terminal menu for common DevAid diagnostics."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    choices = ["analyze", "doctor", "security", "docker", "workflows", "quit"]
    console.print("[bold cyan]DevAid interactive dashboard[/bold cyan]")
    console.print(f"Project: {path.resolve()}")
    while True:
        choice = Prompt.ask(
            "Choose a task",
            choices=choices,
            default="doctor",
        )
        if choice == "quit":
            console.print("Dashboard closed.")
            break
        if choice == "analyze":
            analyze_project(path)
        elif choice == "doctor":
            run_doctor(path)
        elif choice == "security":
            check_security(path)
        elif choice == "docker":
            docker_doctor(path)
        elif choice == "workflows":
            workflow_doctor(path)


@app.command(name="plugins")
def list_plugins() -> None:
    """List installed third-party analyzer plugins without importing them."""
    plugins = discover_analyzer_plugins()
    if not plugins:
        console.print("No analyzer plugins installed.")
        console.print("Register an entry point in the devaid.analyzers group.")
        return
    for plugin in plugins:
        console.print(f"[cyan]{plugin.name}[/cyan] — {plugin.value}")


@app.command(name="plugin-run")
def plugin_run(name: str, path: Path = Path(".")) -> None:
    """Run one explicitly selected installed analyzer plugin."""
    try:
        run_analyzer_plugin(name, path)
    except Exception as error:
        console.print(f"[bold red]Plugin failed:[/bold red] {error}")
        raise typer.Exit(code=1) from error

if __name__ == "__main__":
    app()
