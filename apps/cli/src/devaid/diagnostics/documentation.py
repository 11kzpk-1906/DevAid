from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

REQUIRED_README_SECTIONS = {
    "installation": ("installation", "getting started", "setup"),
    "usage": ("usage", "quick start", "quickstart"),
    "contributing": ("contributing", "contribution"),
    "license": ("license",),
}


def check_documentation(path: Path) -> None:
    """Inspect common project documentation files and README sections."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    checks: list[tuple[str, bool, str]] = []
    readme = path / "README.md"

    if readme.is_file():
        try:
            content = readme.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError) as error:
            checks.append(("README.md", False, f"Could not read file: {error}"))
        else:
            checks.append(
                ("README.md", bool(content.strip()), "File exists and is not empty")
            )
            normalized = content.lower()
            for section, aliases in REQUIRED_README_SECTIONS.items():
                present = any(alias in normalized for alias in aliases)
                checks.append(
                    (
                        f"README section: {section.title()}",
                        present,
                        "Section reference found"
                        if present
                        else f"Consider adding a {section} section",
                    )
                )
    else:
        checks.append(("README.md", False, "Project overview is missing"))

    file_checks = (
        ("CONTRIBUTING.md", "Contribution guidelines"),
        ("LICENSE", "License file"),
        ("CHANGELOG.md", "Changelog"),
        ("CODE_OF_CONDUCT.md", "Code of conduct"),
        ("SECURITY.md", "Security policy"),
    )
    for filename, label in file_checks:
        exists = (path / filename).is_file()
        checks.append(
            (
                label,
                exists,
                f"{filename} found" if exists else f"{filename} not found",
            )
        )

    docs_dir = path / "docs"
    docs_present = docs_dir.is_dir() and any(
        item.is_file() for item in docs_dir.rglob("*")
    )
    checks.append(
        (
            "Documentation directory",
            docs_present,
            "docs/ contains files" if docs_present else "No populated docs/ directory",
        )
    )

    table = Table(title=f"DevAid Documentation Doctor — {path.resolve().name}")
    table.add_column("Check", style="cyan")
    table.add_column("Result")
    table.add_column("Details")

    for label, passed_check, details in checks:
        status = "[green]PASS[/green]" if passed_check else "[yellow]REVIEW[/yellow]"
        table.add_row(label, status, details)

    passed_count = sum(result for _, result, _ in checks)
    total = len(checks)
    score = round((passed_count / total) * 100) if total else 0
    review = total - passed_count

    console.print(table)
    console.print(
        Panel(
            f"[bold]{score}/100[/bold]  •  {passed_count}/{total} checks passed  •  "
            f"{review} items to review",
            title="Documentation score",
            border_style="cyan",
        )
    )
    console.print(
        "[dim]Offline file and heading checks only. DevAid does not judge writing "
        "quality, verify legal compliance, or guarantee documentation accuracy.[/dim]"
    )
