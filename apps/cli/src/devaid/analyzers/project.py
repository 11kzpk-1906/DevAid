"""Basic project structure analyzer."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def analyze_project(path: Path) -> None:
    """Analyze a project's basic structure."""

    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise SystemExit(1)

    markers = {
        "Python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "Node.js": ["package.json"],
        "Rust": ["Cargo.toml"],
        "Go": ["go.mod"],
        "Java": ["pom.xml", "build.gradle"],
    }

    detected = [
        language
        for language, files in markers.items()
        if any((path / file).exists() for file in files)
    ]

    table = Table(title=f"DevAid Project Analysis — {path.resolve().name}")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    table.add_row("Project type", ", ".join(detected) if detected else "Unknown")
    table.add_row("README", "Found" if (path / "README.md").exists() else "Missing")
    table.add_row("Git repository", "Found" if (path / ".git").exists() else "Not found")

    console.print(table)