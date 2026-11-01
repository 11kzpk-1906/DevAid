"""Static JavaScript and Node.js project checks."""
import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def inspect_javascript(root: Path) -> list[tuple[str, str, str]]:
    manifest = root / "package.json"
    if not manifest.is_file():
        return [("INFO", "No Node.js project detected", "package.json was not found at the project root.")]
    try:
        package = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return [("ERROR", "Invalid package.json", "Could not parse a JSON object.")]
    if not isinstance(package, dict):
        return [("ERROR", "Invalid package.json", "The top-level JSON value must be an object.")]
    findings: list[tuple[str, str, str]] = []
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict) or "test" not in scripts:
        findings.append(("REVIEW", "Test script missing", "Consider adding a package.json test script."))
    if not isinstance(package.get("engines"), dict) or not package.get("engines", {}).get("node"):
        findings.append(("INFO", "Node.js version not declared", "Consider declaring engines.node in package.json."))
    ignore = root / ".gitignore"
    if not ignore.is_file():
        findings.append(("REVIEW", ".gitignore missing", "Add node_modules/ and generated output to .gitignore."))
    else:
        try:
            ignored = ignore.read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            ignored = ""
        if "node_modules" not in ignored:
            findings.append(("REVIEW", "node_modules not ignored", "Add node_modules/ to .gitignore."))
    findings.append(("PASS", "package.json parsed", "Static check only; no package scripts were executed."))
    return findings


def javascript_doctor(path: Path = Path(".")) -> None:
    """Review Node.js metadata without installing dependencies or running scripts."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise SystemExit(1)
    findings = inspect_javascript(root)
    table = Table(title=f"JavaScript Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("Finding")
    table.add_column("Details")
    for severity, name, detail in findings:
        table.add_row(severity, name, detail)
    console.print(table)
    console.print(f"Summary: {len(findings)} finding(s). Checks are static and read-only.")
