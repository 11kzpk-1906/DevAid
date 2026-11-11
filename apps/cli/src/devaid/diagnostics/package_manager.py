from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def inspect_packages(root: Path) -> list[tuple[str, str, str]]:
    """Return package-manager findings without installing dependencies."""
    findings: list[tuple[str, str, str]] = []
    py_names = ("pyproject.toml", "requirements.txt", "Pipfile", "setup.py")
    py_lock_names = ("uv.lock", "poetry.lock", "Pipfile.lock", "pdm.lock")
    js_lock_names = (
        "package-lock.json",
        "pnpm-lock.yaml",
        "yarn.lock",
        "bun.lock",
        "bun.lockb",
    )
    py_manifests = [name for name in py_names if (root / name).is_file()]
    py_locks = [name for name in py_lock_names if (root / name).is_file()]
    js_manifest = (root / "package.json").is_file()
    js_locks = [name for name in js_lock_names if (root / name).is_file()]

    if py_manifests and not py_locks:
        findings.append(
            ("REVIEW", "Python lockfile missing", "Add a lockfile for reproducible installs.")
        )
    if len(py_locks) > 1:
        detail = f"Choose one authoritative lockfile: {', '.join(py_locks)}."
        findings.append(("REVIEW", "Multiple Python lockfiles", detail))
    if py_manifests and len(py_locks) == 1:
        findings.append(("PASS", "Python lockfile found", py_locks[0]))
    if js_manifest and not js_locks:
        detail = "Commit the lockfile for your chosen package manager."
        findings.append(("REVIEW", "JavaScript lockfile missing", detail))
    if len(js_locks) > 1:
        detail = f"Choose one authoritative lockfile: {', '.join(js_locks)}."
        findings.append(("REVIEW", "Multiple JavaScript lockfiles", detail))
    if js_manifest and len(js_locks) == 1:
        findings.append(("PASS", "JavaScript lockfile found", js_locks[0]))
    if not py_manifests and not js_manifest:
        detail = "Currently checks common Python and Node.js manifests."
        findings.append(("INFO", "No supported manifest found", detail))
    return findings


def package_doctor(path: Path = Path(".")) -> None:
    """Review dependency manifests and lockfile consistency."""
    root = path.resolve()
    if not root.is_dir():
        console.print("[red]Project directory not found.[/red]")
        raise SystemExit(1)
    table = Table(title=f"Package Manager Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("Finding")
    table.add_column("Details")
    findings = inspect_packages(root)
    for severity, title, detail in findings:
        table.add_row(severity, title, detail)
    console.print(table)
    console.print(f"Summary: {len(findings)} finding(s). Checks are static and read-only.")
