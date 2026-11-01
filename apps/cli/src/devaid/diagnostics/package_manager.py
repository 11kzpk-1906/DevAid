"""Static package manifest and lockfile checks."""
from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def inspect_packages(root: Path) -> list[tuple[str, str, str]]:
    findings: list[tuple[str, str, str]] = []
    py_manifests = [name for name in ("pyproject.toml", "requirements.txt", "Pipfile", "setup.py") if (root / name).is_file()]
    py_locks = [name for name in ("uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock") if (root / name).is_file()]
    js_manifest = (root / "package.json").is_file()
    js_locks = [name for name in ("package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lock", "bun.lockb") if (root / name).is_file()]
    if py_manifests and not py_locks:
        findings.append(("REVIEW", "Python lockfile missing", "Add a lockfile for reproducible installs."))
    if len(py_locks) > 1:
        findings.append(("REVIEW", "Multiple Python lockfiles", f"Choose one authoritative lockfile: {', '.join(py_locks)}."))
    if py_manifests and len(py_locks) == 1:
        findings.append(("PASS", "Python lockfile found", py_locks[0]))
    if js_manifest and not js_locks:
        findings.append(("REVIEW", "JavaScript lockfile missing", "Commit the lockfile for your chosen package manager."))
    if len(js_locks) > 1:
        findings.append(("REVIEW", "Multiple JavaScript lockfiles", f"Choose one authoritative lockfile: {', '.join(js_locks)}."))
    if js_manifest and len(js_locks) == 1:
        findings.append(("PASS", "JavaScript lockfile found", js_locks[0]))
    if not py_manifests and not js_manifest:
        findings.append(("INFO", "No supported manifest found", "Currently checks common Python and Node.js manifests."))
    return findings


def package_doctor(path: Path = Path(".")) -> None:
    """Review dependency manifests and lockfile consistency."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise SystemExit(1)
    _display(inspect_packages(root), "Package Manager Doctor", root)


def _display(findings: list[tuple[str, str, str]], title: str, root: Path) -> None:
    table = Table(title=f"{title} — {root.name}")
    table.add_column("Status")
    table.add_column("Finding")
    table.add_column("Details")
    for severity, name, detail in findings:
        table.add_row(severity, name, detail)
    console.print(table)
    console.print(f"Summary: {len(findings)} finding(s). Checks are static and read-only.")
