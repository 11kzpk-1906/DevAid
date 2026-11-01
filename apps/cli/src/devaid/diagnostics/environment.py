"""Local development environment diagnostics."""

import platform
import shutil
import sys
from importlib.util import find_spec

from rich.console import Console
from rich.table import Table

console = Console()


def check_environment() -> None:
    """Report the current Python environment and available developer tools."""
    python_version = platform.python_version()
    implementation = platform.python_implementation()
    in_venv = sys.prefix != sys.base_prefix

    checks: list[tuple[str, str, str]] = [
        (
            "Python runtime",
            "PASS",
            f"{implementation} {python_version}",
        ),
        (
            "Python executable",
            "INFO",
            sys.executable,
        ),
        (
            "Virtual environment",
            "PASS" if in_venv else "REVIEW",
            "Active" if in_venv else "Not detected; consider using a project environment",
        ),
        ("Operating system", "INFO", f"{platform.system()} {platform.release()}"),
    ]

    for tool in ("uv", "pip", "node", "npm", "pnpm", "git"):
        available = (
            find_spec("pip") is not None
            if tool == "pip"
            else shutil.which(tool) is not None
        )
        checks.append(
            (
                tool,
                "PASS" if available else "INFO",
                "Available on PATH" if available else "Not detected on PATH",
            )
        )

    table = Table(title="DevAid Environment Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    for label, status, details in checks:
        style = {"PASS": "green", "REVIEW": "yellow", "INFO": "blue"}[status]
        table.add_row(label, f"[{style}]{status}[/{style}]", details)

    console.print(table)
    available_tools = sum(status == "PASS" for _, status, _ in checks)
    console.print(
        f"\n[bold]Runtime:[/bold] Python {python_version} • "
        f"{'virtual environment active' if in_venv else 'no virtual environment detected'}"
    )
    console.print(
        f"[dim]Detected {available_tools} available runtime/tool checks. "
        "This is an informational local snapshot; it does not install, modify, "
        "or execute any tools.[/dim]"
    )
