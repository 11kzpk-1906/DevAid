"""Offline checks for GitHub Actions workflow hygiene."""

import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
WORKFLOW_DIR = Path(".github/workflows")
ACTION_PATTERN = re.compile(r"^\s*uses:\s*([^\s#]+)", re.MULTILINE)
SHA_PATTERN = re.compile(r"@[0-9a-fA-F]{40}$")


def workflow_doctor(path: Path) -> None:
    """Inspect GitHub Actions workflows for common security and reliability issues."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    workflow_root = root / WORKFLOW_DIR
    if not workflow_root.is_dir():
        console.print(
            f"[yellow]No GitHub Actions workflows found at "
            f"{WORKFLOW_DIR.as_posix()}.[/yellow]"
        )
        return

    workflows = sorted(
        file_path
        for file_path in workflow_root.rglob("*")
        if file_path.is_file() and file_path.suffix.lower() in {".yml", ".yaml"}
    )
    if not workflows:
        console.print("[yellow]No YAML workflow files found.[/yellow]")
        return

    findings: list[tuple[str, str, str]] = []
    for workflow in workflows:
        relative = workflow.relative_to(root).as_posix()
        try:
            content = workflow.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            findings.append(("REVIEW", relative, "Could not read this workflow file"))
            continue

        if re.search(r"^\s*permissions\s*:", content, re.MULTILINE):
            findings.append(
                ("PASS", relative, "Explicit workflow or job permissions are declared")
            )
        else:
            findings.append(
                (
                    "REVIEW",
                    relative,
                    "Declare least-privilege permissions explicitly",
                )
            )

        actions = ACTION_PATTERN.findall(content)
        unpinned = [
            action
            for action in actions
            if not action.startswith("./") and not SHA_PATTERN.search(action)
        ]
        if unpinned:
            findings.append(
                (
                    "REVIEW",
                    relative,
                    f"{len(unpinned)} action reference(s) use a tag or branch "
                    "instead of a full commit SHA",
                )
            )
        elif actions:
            findings.append(
                ("PASS", relative, "Third-party actions are pinned to full commit SHAs")
            )

        if "actions/checkout@" in content and not re.search(
            r"^\s* persist-credentials:\s*false\s*$",
            content,
            re.MULTILINE,
        ):
            findings.append(
                (
                    "REVIEW",
                    relative,
                    "Consider setting persist-credentials: false when later steps "
                    "do not need Git authentication",
                )
            )

    table = Table(title=f"DevAid Workflow Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("Workflow", style="cyan")
    table.add_column("Finding")
    styles = {"PASS": "green", "REVIEW": "yellow"}
    for status, filename, details in findings:
        style = styles[status]
        table.add_row(f"[{style}]{status}[/{style}]", filename, details)
    console.print(table)

    passed = sum(item[0] == "PASS" for item in findings)
    review = sum(item[0] == "REVIEW" for item in findings)
    console.print(
        Panel(
            f"{len(workflows)} workflow files checked • {passed} passed • "
            f"{review} items to review",
            title="Workflow hygiene summary",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Local, read-only heuristic checks. Review each recommendation against "
        "your workflow's needs; no files are changed and nothing is uploaded.[/dim]"
    )
