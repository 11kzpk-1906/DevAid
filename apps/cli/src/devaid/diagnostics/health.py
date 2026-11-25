from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

DEPENDENCY_MANIFESTS = (
    "pyproject.toml",
    "requirements.txt",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "pom.xml",
    "build.gradle",
)
TEST_DIRECTORIES = ("tests", "test")


def _has_tests(path: Path) -> bool:
    """Return whether the project contains a recognizable test file."""
    for directory_name in TEST_DIRECTORIES:
        directory = path / directory_name
        if directory.is_dir() and any(directory.rglob("test_*.py")):
            return True
        if directory.is_dir() and any(directory.rglob("*_test.py")):
            return True

    return any(path.glob("test_*.py")) or any(path.glob("*_test.py"))


def health_check(path: Path) -> None:
    """Generate a transparent, offline health report for a project."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    checks = [
        ("README documentation", (path / "README.md").is_file()),
        ("Git version control", (path / ".git").exists()),
        (
            "Dependency manifest",
            any((path / name).is_file() for name in DEPENDENCY_MANIFESTS),
        ),
        ("Test files", _has_tests(path)),
        (
            "Continuous integration",
            (path / ".github" / "workflows").is_dir()
            and any((path / ".github" / "workflows").glob("*.yml"))
            or (path / ".github" / "workflows").is_dir()
            and any((path / ".github" / "workflows").glob("*.yaml")),
        ),
        (
            "Contributor guidance",
            (path / "CONTRIBUTING.md").is_file()
            or (path / "docs" / "CONTRIBUTING.md").is_file(),
        ),
    ]

    passed = sum(is_healthy for _, is_healthy in checks)
    total = len(checks)
    score = round((passed / total) * 100)

    table = Table(title=f"DevAid Project Health — {path.resolve().name}")
    table.add_column("Check", style="cyan")
    table.add_column("Result")

    for label, is_healthy in checks:
        result = "[green]PASS[/green]" if is_healthy else "[yellow]REVIEW[/yellow]"
        table.add_row(label, result)

    console.print(table)

    if score >= 80:
        status = "[bold green]Healthy[/bold green]"
    elif score >= 50:
        status = "[bold yellow]Needs attention[/bold yellow]"
    else:
        status = "[bold red]Needs work[/bold red]"

    console.print(
        Panel(
            f"[bold]{score}/100[/bold]  •  {passed}/{total} checks passed\n{status}",
            title="Health score",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Local, rule-based checks only. This score is a guidance snapshot, "
        "not a security audit or a guarantee of software quality.[/dim]"
    )
