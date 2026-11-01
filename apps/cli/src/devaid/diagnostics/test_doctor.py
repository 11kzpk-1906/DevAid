"""Offline test-suite readiness checks for common project ecosystems."""

import json
import tomllib
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

TEST_DIRECTORIES = ("tests", "test", "__tests__")


def _has_python_tests(path: Path) -> bool:
    """Find common Python test files without traversing virtual environments."""
    for directory_name in ("tests", "test"):
        directory = path / directory_name
        if directory.is_dir() and (
            any(directory.rglob("test_*.py")) or any(directory.rglob("*_test.py"))
        ):
            return True
    return any(path.glob("test_*.py")) or any(path.glob("*_test.py"))


def _has_javascript_tests(path: Path) -> bool:
    """Find common JavaScript and TypeScript test files in conventional folders."""
    for directory_name in ("tests", "test", "__tests__", "src"):
        directory = path / directory_name
        if not directory.is_dir():
            continue
        for pattern in ("*.test.js", "*.test.jsx", "*.test.ts", "*.test.tsx",
                        "*.spec.js", "*.spec.ts"):
            if any(directory.rglob(pattern)):
                return True
    return any(
        any(path.glob(pattern))
        for pattern in ("*.test.js", "*.test.ts", "*.spec.js", "*.spec.ts")
    )


def _check_python(path: Path, rows: list[tuple[str, str, str]]) -> None:
    manifest = path / "pyproject.toml"
    requirements = path / "requirements.txt"
    if not manifest.is_file() and not requirements.is_file():
        return

    rows.append(("Python", "INFO", "Python project manifest detected"))
    if _has_python_tests(path):
        rows.append(("Python tests", "PASS", "Python test files detected"))
    else:
        rows.append(
            ("Python tests", "REVIEW", "No test_*.py or *_test.py files found")
        )

    runner_configured = (path / "pytest.ini").is_file() or (path / "tox.ini").is_file()
    if manifest.is_file():
        try:
            with manifest.open("rb") as file:
                data = tomllib.load(file)
            runner_configured = runner_configured or "pytest" in data.get("tool", {})
        except (OSError, tomllib.TOMLDecodeError):
            rows.append(("Python test config", "REVIEW", "Could not parse pyproject.toml"))

    if runner_configured:
        rows.append(("Python test runner", "PASS", "Pytest configuration detected"))
    else:
        rows.append(
            ("Python test runner", "INFO", "No pytest config detected; unittest needs none")
        )


def _check_javascript(path: Path, rows: list[tuple[str, str, str]]) -> None:
    manifest = path / "package.json"
    if not manifest.is_file():
        return

    rows.append(("JavaScript", "INFO", "package.json detected"))
    try:
        data = json.loads(manifest.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        rows.append(("JavaScript test setup", "ERROR", "package.json is not valid JSON"))
        return

    scripts = data.get("scripts", {})
    if not isinstance(scripts, dict):
        rows.append(("JavaScript test script", "ERROR", "scripts must be a JSON object"))
        return

    if scripts.get("test"):
        rows.append(("JavaScript test script", "PASS", "A test script is defined"))
    else:
        rows.append(
            ("JavaScript test script", "REVIEW", "Add a test script to package.json")
        )

    if _has_javascript_tests(path):
        rows.append(("JavaScript test files", "PASS", "Common test files detected"))
    else:
        rows.append(
            ("JavaScript test files", "REVIEW", "No common .test or .spec files found")
        )


def _check_rust(path: Path, rows: list[tuple[str, str, str]]) -> None:
    if not (path / "Cargo.toml").is_file():
        return

    rows.append(("Rust", "INFO", "Cargo.toml detected"))
    if (path / "tests").is_dir():
        rows.append(("Rust integration tests", "PASS", "tests/ directory detected"))
    else:
        rows.append(
            ("Rust integration tests", "INFO", "No tests/ directory; unit tests may live in source")
        )


def _check_go(path: Path, rows: list[tuple[str, str, str]]) -> None:
    if not (path / "go.mod").is_file():
        return

    rows.append(("Go", "INFO", "go.mod detected"))
    if any(path.rglob("*_test.go")):
        rows.append(("Go tests", "PASS", "Go test files detected"))
    else:
        rows.append(("Go tests", "REVIEW", "No *_test.go files found"))


def inspect_tests(path: Path) -> list[tuple[str, str, str]]:
    """Return test readiness findings without running tests or executing project code."""
    rows: list[tuple[str, str, str]] = []
    _check_python(path, rows)
    _check_javascript(path, rows)
    _check_rust(path, rows)
    _check_go(path, rows)

    workflows = path / ".github" / "workflows"
    if workflows.is_dir():
        workflow_files = list(workflows.glob("*.yml")) + list(workflows.glob("*.yaml"))
        if workflow_files:
            workflow_text = ""
            for workflow in workflow_files:
                try:
                    workflow_text += workflow.read_text(encoding="utf-8").lower() + "\n"
                except (OSError, UnicodeDecodeError):
                    continue
            test_commands = ("pytest", "python -m unittest", "npm test",
                             "pnpm test", "yarn test", "cargo test", "go test")
            if any(command in workflow_text for command in test_commands):
                rows.append(("CI test step", "PASS", "A recognized test command appears in CI"))
            else:
                rows.append(
                    ("CI test step", "REVIEW", "No recognized test command found in workflow files")
                )
    else:
        rows.append(("CI test step", "REVIEW", "No GitHub Actions workflow directory found"))

    return rows


def test_doctor(path: Path) -> None:
    """Display test-suite readiness without executing any tests."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings = inspect_tests(path)
    if not findings:
        console.print(
            "[yellow]No supported project manifest detected.[/yellow] "
            "Supported ecosystems: Python, JavaScript/TypeScript, Rust, and Go."
        )
        return

    table = Table(title=f"DevAid Test Doctor — {path.resolve().name}")
    table.add_column("Area", style="cyan")
    table.add_column("Status")
    table.add_column("Details")

    styles = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}
    for area, status, details in findings:
        style = styles[status]
        table.add_row(area, f"[{style}]{status}[/{style}]", details)

    console.print(table)
    passed = sum(status == "PASS" for _, status, _ in findings)
    review = sum(status == "REVIEW" for _, status, _ in findings)
    errors = sum(status == "ERROR" for _, status, _ in findings)
    console.print(
        f"\n[bold]Summary:[/bold] {passed} passed • {review} to review • {errors} errors"
    )
    console.print(
        "[dim]Static, offline checks only. DevAid does not run tests, install packages, "
        "or modify project files.[/dim]"
    )
