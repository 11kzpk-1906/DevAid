"""Actionable, offline recommendations for common project gaps."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def collect_suggestions(path: Path) -> list[tuple[str, str, str]]:
    """Return prioritized recommendations using project structure only."""
    suggestions: list[tuple[str, str, str]] = []

    if not (path / "README.md").is_file():
        suggestions.append(
            ("HIGH", "Add a README", "Create README.md with setup, usage, and project details.")
        )

    has_tests = any((path / name).is_dir() for name in ("tests", "test"))
    has_root_tests = any(path.glob("test_*.py")) or any(path.glob("*_test.py"))
    if not has_tests and not has_root_tests:
        suggestions.append(
            ("HIGH", "Add automated tests", "Create a tests/ directory and add tests for core behavior.")
        )

    gitignore = path / ".gitignore"
    if not gitignore.is_file():
        suggestions.append(
            ("HIGH", "Add a .gitignore", "Ignore virtual environments, build output, caches, and local secrets.")
        )
    else:
        try:
            entries = {
                line.strip()
                for line in gitignore.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            }
            for pattern, advice in (
                (".env", "Add .env to .gitignore to reduce accidental secret commits."),
                (".venv/", "Add .venv/ to .gitignore to keep local environments out of Git."),
                ("node_modules/", "Add node_modules/ to .gitignore for Node.js projects."),
            ):
                if pattern not in entries and (
                    pattern != "node_modules/" or (path / "package.json").is_file()
                ):
                    suggestions.append(("MEDIUM", "Review .gitignore", advice))
        except (OSError, UnicodeError):
            suggestions.append(
                ("MEDIUM", "Check .gitignore encoding", "Make .gitignore readable as UTF-8.")
            )

    workflows = path / ".github" / "workflows"
    if not workflows.is_dir() or not (
        any(workflows.glob("*.yml")) or any(workflows.glob("*.yaml"))
    ):
        suggestions.append(
            ("MEDIUM", "Add continuous integration", "Run linting and automated tests on every pull request.")
        )

    if not (path / "CONTRIBUTING.md").is_file() and not (
        path / "docs" / "CONTRIBUTING.md"
    ).is_file():
        suggestions.append(
            ("LOW", "Add contribution guidance", "Explain how contributors can set up, test, and submit changes.")
        )

    return suggestions


def show_suggestions(path: Path) -> None:
    """Display prioritized recommendations without modifying project files."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise SystemExit(1)

    findings = collect_suggestions(path)
    table = Table(title=f"DevAid Fix Suggestions — {path.resolve().name}")
    table.add_column("Priority", style="cyan")
    table.add_column("Recommendation")
    table.add_column("Suggested action")

    for priority, title, action in findings:
        style = {"HIGH": "red", "MEDIUM": "yellow", "LOW": "blue"}[priority]
        table.add_row(f"[{style}]{priority}[/{style}]", title, action)

    console.print(table)
    if findings:
        console.print(
            f"\n[bold]{len(findings)} recommendation(s)[/bold] to review. "
            "DevAid suggests changes but never applies them automatically."
        )
    else:
        console.print("[bold green]No recommendations from the current rule set.[/bold green]")
    console.print(
        "[dim]Offline, rule-based guidance based on project structure. "
        "Recommendations are not a complete code or security review.[/dim]"
    )
