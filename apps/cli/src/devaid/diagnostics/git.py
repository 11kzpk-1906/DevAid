import subprocess
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()


def _run_git(path: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    """Run a fixed, read-only Git command without invoking a shell."""
    return subprocess.run(
        ["git", *arguments],
        cwd=path,
        capture_output=True,
        text=True,
        check=False,
        timeout=5,
    )


def _git_result(path: Path, *arguments: str) -> subprocess.CompletedProcess[str] | None:
    """Run Git safely and report unavailable or timed-out installations."""
    try:
        return _run_git(path, *arguments)
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


def inspect_git(path: Path) -> list[tuple[str, str, str]]:
    """Return repository status findings without changing Git state."""
    root_result = _git_result(path, "rev-parse", "--show-toplevel")
    if root_result is None:
        return [("Git", "ERROR", "Git is unavailable or did not respond within 5 seconds")]
    if root_result.returncode != 0:
        return [("Repository", "REVIEW", "This directory is not inside a Git repository")]

    findings: list[tuple[str, str, str]] = [
        ("Repository", "PASS", "Git working tree detected")
    ]

    branch_result = _git_result(path, "branch", "--show-current")
    if branch_result is None or branch_result.returncode != 0:
        findings.append(("Current branch", "REVIEW", "Could not determine the current branch"))
    elif branch_result.stdout.strip():
        findings.append(("Current branch", "PASS", branch_result.stdout.strip()))
    else:
        findings.append(("Current branch", "REVIEW", "Detached HEAD; no branch is checked out"))

    status_result = _git_result(path, "status", "--short", "--branch", "--untracked-files=normal")
    if status_result is None or status_result.returncode != 0:
        findings.append(("Working tree", "ERROR", "Could not read Git working-tree status"))
    else:
        status_lines = status_result.stdout.splitlines()
        changes = [line for line in status_lines if not line.startswith("##")]
        staged = sum(line[0:1] not in (" ", "?") for line in changes)
        unstaged = sum(line[1:2] not in (" ", "?") for line in changes)
        untracked = sum(line.startswith("??") for line in changes)

        if not changes:
            findings.append(("Working tree", "PASS", "No staged, modified, or untracked changes"))
        else:
            findings.append(
                ("Working tree", "REVIEW",
                 f"{staged} staged, {unstaged} unstaged, {untracked} untracked change(s)")
            )

    remote_result = _git_result(path, "remote")
    if remote_result is None or remote_result.returncode != 0:
        findings.append(("Remotes", "REVIEW", "Could not inspect configured remote names"))
    else:
        remotes = [name for name in remote_result.stdout.splitlines() if name.strip()]
        if remotes:
            findings.append(("Remotes", "PASS", f"{len(remotes)} remote(s): {', '.join(remotes)}"))
        else:
            findings.append(("Remotes", "INFO", "No Git remotes configured"))

    name_result = _git_result(path, "config", "--get", "user.name")
    email_result = _git_result(path, "config", "--get", "user.email")
    identity_ready = (
        name_result is not None
        and email_result is not None
        and name_result.returncode == 0
        and email_result.returncode == 0
        and bool(name_result.stdout.strip())
        and bool(email_result.stdout.strip())
    )
    if identity_ready:
        findings.append(("Commit identity", "PASS", "Git author name and email are configured"))
    else:
        findings.append(("Commit identity", "REVIEW", "Configure Git user.name and user.email"))

    return findings


def git_doctor(path: Path) -> None:
    """Display read-only Git repository diagnostics."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings = inspect_git(path)
    table = Table(title=f"DevAid Git Doctor — {path.resolve().name}")
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
    console.print(
        f"\n[bold]Summary:[/bold] {passed} passed • {review} to review • {errors} errors"
    )
    console.print(
        "[dim]Read-only checks. DevAid does not stage, commit, push, switch branches, "
        "or display remote URLs or configured identity values.[/dim]"
    )
