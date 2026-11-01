"""Static Python project convention checks."""
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def inspect_python(root: Path) -> list[tuple[str, str, str]]:
    manifests = ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")
    if not any((root / name).exists() for name in manifests):
        return [("INFO", "No Python project detected", "No common Python manifest found at the root.")]
    findings: list[tuple[str, str, str]] = []
    if not (root / "pyproject.toml").is_file():
        findings.append(("REVIEW", "pyproject.toml missing", "Consider centralising project and tool configuration."))
    if not any((root / name).is_dir() for name in ("tests", "test")):
        findings.append(("REVIEW", "Test directory missing", "Consider adding tests/ for automated tests."))
    requirements = root / "requirements.txt"
    if requirements.is_file():
        try:
            lines = requirements.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            lines = []
        unpinned = [
            line.strip() for line in lines
            if line.strip() and not line.lstrip().startswith(("#", "-"))
            and not any(op in line for op in ("==", ">=", "<=", "~=", "!=", ">", "<"))
        ]
        if unpinned:
            findings.append(("REVIEW", "Unpinned requirements", f"{len(unpinned)} item(s) have no version constraint."))
    if (root / ".venv").exists() or (root / "venv").exists():
        findings.append(("REVIEW", "Virtual environment directory found", "Ensure .venv/ or venv/ is ignored by Git."))
    if not findings:
        findings.append(("PASS", "Basic Python structure found", "No issues detected by these lightweight checks."))
    return findings


def python_doctor(path: Path = Path(".")) -> None:
    """Review Python project conventions without executing project code."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise SystemExit(1)
    _display(inspect_python(root), root)


def _display(findings: list[tuple[str, str, str]], root: Path) -> None:
    table = Table(title=f"Python Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("Finding")
    table.add_column("Details")
    for severity, name, detail in findings:
        table.add_row(severity, name, detail)
    console.print(table)
    console.print(f"Summary: {len(findings)} finding(s). Checks are static and read-only.")
