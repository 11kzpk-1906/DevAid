from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def inspect_python(root: Path) -> list[tuple[str, str, str]]:
    """Return Python project findings without importing project code."""
    manifests = ("pyproject.toml", "requirements.txt", "setup.py", "Pipfile")
    if not any((root / name).exists() for name in manifests):
        detail = "No common Python manifest found at the project root."
        return [("INFO", "No Python project detected", detail)]
    findings: list[tuple[str, str, str]] = []
    if not (root / "pyproject.toml").is_file():
        detail = "Consider centralising project and tool configuration."
        findings.append(("REVIEW", "pyproject.toml missing", detail))
    if not any((root / name).is_dir() for name in ("tests", "test")):
        findings.append(
            ("REVIEW", "Test directory missing", "Consider adding tests/ for automation.")
        )
    requirements = root / "requirements.txt"
    if requirements.is_file():
        try:
            lines = requirements.read_text(encoding="utf-8").splitlines()
        except (OSError, UnicodeError):
            lines = []
        unpinned = [
            line.strip()
            for line in lines
            if line.strip()
            and not line.lstrip().startswith(("#", "-"))
            and not any(op in line for op in ("==", ">=", "<=", "~=", "!=", ">", "<"))
        ]
        if unpinned:
            detail = f"{len(unpinned)} item(s) have no version constraint."
            findings.append(("REVIEW", "Unpinned requirements", detail))
    if (root / ".venv").exists() or (root / "venv").exists():
        detail = "Ensure the virtual environment directory is ignored by Git."
        findings.append(("REVIEW", "Virtual environment directory found", detail))
    if not findings:
        detail = "No issues detected by these lightweight checks."
        findings.append(("PASS", "Basic Python structure found", detail))
    return findings


def python_doctor(path: Path = Path(".")) -> None:
    """Review Python project conventions without executing project code."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise SystemExit(1)
    findings = inspect_python(root)
    table = Table(title=f"Python Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("Finding")
    table.add_column("Details")
    for severity, title, detail in findings:
        table.add_row(severity, title, detail)
    console.print(table)
    console.print(f"Summary: {len(findings)} finding(s). Checks are static and read-only.")
