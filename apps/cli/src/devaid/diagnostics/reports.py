"""Export local project diagnostics as Markdown or JSON."""
import json
from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from devaid.diagnostics.javascript import inspect_javascript
from devaid.diagnostics.package_manager import inspect_packages
from devaid.diagnostics.python_project import inspect_python

console = Console()


def _items(category: str, findings: list[tuple[str, str, str]]) -> list[dict[str, str]]:
    return [
        {"category": category, "severity": level, "title": title, "detail": detail}
        for level, title, detail in findings
    ]


def report(
    path: Annotated[Path, typer.Argument(help="Project directory to inspect.")] = Path("."),
    output_format: Annotated[
        str, typer.Option("--format", help="Report format: markdown or json.")
    ] = "markdown",
    output: Annotated[
        Path | None, typer.Option("--output", help="Optional output file path.")
    ] = None,
) -> None:
    """Export package, Python, and JavaScript findings to a file or stdout."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise typer.Exit(code=1)
    if output_format not in {"markdown", "json"}:
        raise typer.BadParameter("format must be 'markdown' or 'json'")
    findings = (
        _items("Package Manager", inspect_packages(root))
        + _items("Python", inspect_python(root))
        + _items("JavaScript", inspect_javascript(root))
    )
    summary = {
        level: sum(item["severity"] == level for item in findings)
        for level in ("ERROR", "REVIEW", "PASS", "INFO")
    }
    if output_format == "json":
        content = json.dumps(
            {"project": root.name, "findings": findings, "summary": summary},
            indent=2,
        ) + "\n"
    else:
        lines = [
            f"# DevAid Report — {root.name}",
            "",
            "> Static local checks only. Findings are guidance, not a security guarantee.",
            "",
            "## Summary",
            "",
            *[f"- {key.title()}: {value}" for key, value in summary.items()],
            "",
            "## Findings",
            "",
        ]
        for item in findings:
            lines.extend([
                f"### [{item['severity']}] {item['title']}",
                "",
                f"- Category: {item['category']}",
                f"- Detail: {item['detail']}",
                "",
            ])
        content = "\n".join(lines)
    if output is None:
        console.print(content)
    else:
        destination = output.resolve()
        destination.write_text(content, encoding="utf-8")
        console.print(f"[green]Report written to[/green] {destination}")
