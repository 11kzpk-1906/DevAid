"""Transparent, offline security posture scoring for local projects."""

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from devaid.diagnostics.security import _tracked_sensitive_files
from devaid.diagnostics.security_code import (
    IGNORED_DIRS,
    JS_RULES,
    MAX_FILE_BYTES,
    MAX_FILES,
    SOURCE_SUFFIXES,
    _python_findings,
)

console = Console(width=140)

# Weights total 100. Checks that cannot be assessed are excluded from the
# denominator rather than being silently treated as passing.
WEIGHTS = {
    "Environment ignore rules": 15,
    "Git-tracked sensitive files": 20,
    "Security policy": 10,
    "Dependabot": 10,
    "CodeQL workflow": 15,
    "CI workflow": 10,
    "Static source scan": 20,
}


def _workflow_files(root: Path) -> list[Path]:
    workflow_dir = root / ".github" / "workflows"
    if not workflow_dir.is_dir():
        return []
    return [
        item for item in workflow_dir.iterdir()
        if item.is_file() and item.suffix.lower() in {".yml", ".yaml"}
    ]


def evaluate_security_posture(
    root: Path,
) -> tuple[int, int, list[tuple[str, str, int, int, str]]]:
    """Return score, assessed weight, and check rows.

    Each row is (control, status, weight, points_earned, explanation).
    INFO rows have zero weight and are excluded from the score denominator.
    """
    rows: list[tuple[str, str, int, int, str]] = []

    ignore_file = root / ".gitignore"
    try:
        ignore_lines = {
            line.strip()
            for line in ignore_file.read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        } if ignore_file.is_file() else set()
    except (OSError, UnicodeDecodeError):
        ignore_lines = set()
    protects_env = any(
        rule in ignore_lines for rule in (".env", ".env.*", "*.env")
    )
    weight = WEIGHTS["Environment ignore rules"]
    rows.append((
        "Environment ignore rules",
        "PASS" if protects_env else "REVIEW",
        weight,
        weight if protects_env else 0,
        "Environment-file patterns are ignored"
        if protects_env else "Add .env and .env.* to .gitignore",
    ))

    if (root / ".git").exists():
        tracked = _tracked_sensitive_files(root)
        weight = WEIGHTS["Git-tracked sensitive files"]
        rows.append((
            "Git-tracked sensitive files",
            "ERROR" if tracked else "PASS",
            weight,
            0 if tracked else weight,
            f"{len(tracked)} sensitive-looking path(s) are tracked"
            if tracked else "No configured sensitive filenames are tracked",
        ))
    else:
        rows.append((
            "Git-tracked sensitive files", "INFO", 0, 0,
            "Not a Git working tree; tracked-file status was not assessed",
        ))

    security_policy = (root / "SECURITY.md").is_file() or (
        root / ".github" / "SECURITY.md"
    ).is_file()
    weight = WEIGHTS["Security policy"]
    rows.append((
        "Security policy",
        "PASS" if security_policy else "REVIEW",
        weight,
        weight if security_policy else 0,
        "A SECURITY.md policy is present"
        if security_policy else "Add SECURITY.md with a vulnerability-reporting process",
    ))

    dependabot = (root / ".github" / "dependabot.yml").is_file() or (
        root / ".github" / "dependabot.yaml"
    ).is_file()
    weight = WEIGHTS["Dependabot"]
    rows.append((
        "Dependabot",
        "PASS" if dependabot else "REVIEW",
        weight,
        weight if dependabot else 0,
        "Dependabot configuration is present"
        if dependabot else "Add .github/dependabot.yml to check dependency updates",
    ))

    workflows = _workflow_files(root)
    workflow_text = ""
    for workflow in workflows:
        try:
            workflow_text += workflow.read_text(encoding="utf-8").lower() + "\n"
        except (OSError, UnicodeDecodeError):
            continue

    codeql = "codeql" in workflow_text
    weight = WEIGHTS["CodeQL workflow"]
    rows.append((
        "CodeQL workflow",
        "PASS" if codeql else "REVIEW",
        weight,
        weight if codeql else 0,
        "A workflow references CodeQL analysis"
        if codeql else "Add a GitHub CodeQL workflow for supported source languages",
    ))

    ci_present = bool(workflows)
    weight = WEIGHTS["CI workflow"]
    rows.append((
        "CI workflow",
        "PASS" if ci_present else "REVIEW",
        weight,
        weight if ci_present else 0,
        f"{len(workflows)} GitHub Actions workflow file(s) found"
        if ci_present else "Add automated tests and lint checks in GitHub Actions",
    ))

    scanned = 0
    errors = 0
    reviews = 0
    for current, directories, filenames in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRS]
        for filename in filenames:
            source_path = Path(current) / filename
            if source_path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            try:
                if source_path.stat().st_size > MAX_FILE_BYTES:
                    continue
                source = source_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            relative = source_path.relative_to(root).as_posix()
            if source_path.suffix.lower() == ".py":
                findings = _python_findings(source, relative)
            else:
                findings = []
                for severity, pattern, message in JS_RULES:
                    for match in pattern.finditer(source):
                        line = source.count("\n", 0, match.start()) + 1
                        findings.append((severity, relative, line, message))
            errors += sum(item[0] == "ERROR" for item in findings)
            reviews += sum(item[0] == "REVIEW" for item in findings)
            if scanned >= MAX_FILES:
                break
        if scanned >= MAX_FILES:
            break

    if scanned == 0:
        rows.append((
            "Static source scan", "INFO", 0, 0,
            "No supported source files found; static scan was not scored",
        ))
    else:
        weight = WEIGHTS["Static source scan"]
        penalty = min(weight, errors * 5 + reviews * 2)
        status = "ERROR" if errors else "REVIEW" if reviews else "PASS"
        rows.append((
            "Static source scan",
            status,
            weight,
            weight - penalty,
            f"{scanned} file(s) scanned; {errors} high-risk pattern(s), "
            f"{reviews} review item(s)",
        ))

    assessed_weight = sum(row[2] for row in rows)
    earned = sum(row[3] for row in rows)
    score = round(earned / assessed_weight * 100) if assessed_weight else 0
    return score, assessed_weight, rows


def security_score(path: Path) -> None:
    """Calculate a local security posture score and show actionable checks."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    score, assessed_weight, rows = evaluate_security_posture(root)
    table = Table(title=f"DevAid Security Score — {root.name}")
    table.add_column("Status")
    table.add_column("Control", style="cyan")
    table.add_column("Weight", justify="right")
    table.add_column("Points", justify="right")
    table.add_column("Finding")
    styles = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}
    for control, status, weight, earned, detail in rows:
        table.add_row(
            f"[{styles[status]}]{status}[/{styles[status]}]",
            control,
            f"{weight}%" if weight else "—",
            f"{earned}/{weight}" if weight else "N/A",
            detail,
        )
    console.print(table)
    console.print(Panel(
        f"[bold cyan]{score}/100[/bold cyan]  •  {assessed_weight}/100 weight assessed",
        title="Security posture score",
        border_style="cyan",
    ))
    console.print(
        "[dim]Local, read-only heuristics—not a security certification or audit. "
        "INFO checks are excluded from the denominator, and findings may be "
        "incomplete or produce false positives. Source is never executed or uploaded.[/dim]"
    )
