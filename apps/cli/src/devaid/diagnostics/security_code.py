"""Static, local-first checks for risky source-code patterns."""

import ast
import os
import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(width=140)
IGNORED_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", ".tox",
}
SOURCE_SUFFIXES = {".py", ".js", ".jsx", ".mjs", ".cjs", ".ts", ".tsx"}
MAX_FILE_BYTES = 1_000_000
MAX_FILES = 5_000

JS_RULES: tuple[tuple[str, re.Pattern[str], str], ...] = (
    (
        "ERROR",
        re.compile(r"\beval\s*\("),
        "Dynamic eval() executes generated code; avoid it where possible",
    ),
    (
        "REVIEW",
        re.compile(r"\.innerHTML\s*="),
        "Assigning innerHTML can introduce cross-site scripting; prefer textContent or safe DOM APIs",
    ),
    (
        "ERROR",
        re.compile(r"\bchild_process\.(?:exec|execSync)\s*\("),
        "Review shell command construction; untrusted input can cause command injection",
    ),
    (
        "REVIEW",
        re.compile(r"\bnew\s+Function\s*\("),
        "The Function constructor dynamically executes code",
    ),
)


def _python_findings(source: str, relative: str) -> list[tuple[str, str, int, str]]:
    findings: list[tuple[str, str, int, str]] = []
    try:
        tree = ast.parse(source)
    except SyntaxError as error:
        return [
            ("INFO", relative, error.lineno or 0,
             "Python source could not be parsed; static checks skipped")
        ]

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = ""
        if isinstance(node.func, ast.Name):
            name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            owner = node.func.value
            prefix = owner.id if isinstance(owner, ast.Name) else ""
            name = f"{prefix}.{node.func.attr}" if prefix else node.func.attr

        if name in {"eval", "exec"}:
            findings.append((
                "ERROR", relative, node.lineno,
                f"Use of {name}() dynamically executes code; validate inputs and avoid dynamic evaluation",
            ))
        elif name == "os.system":
            findings.append((
                "ERROR", relative, node.lineno,
                "os.system() invokes a shell; prefer subprocess with an argument list",
            ))
        elif name in {"pickle.load", "pickle.loads"}:
            findings.append((
                "ERROR", relative, node.lineno,
                "pickle can execute code while deserializing; never load untrusted data",
            ))
        elif name == "yaml.load":
            safe_loader = any(keyword.arg == "Loader" for keyword in node.keywords)
            if not safe_loader:
                findings.append((
                    "ERROR", relative, node.lineno,
                    "yaml.load() without an explicit safe loader can construct unsafe objects",
                ))
        elif name in {"subprocess.run", "subprocess.call", "subprocess.Popen"}:
            shell_true = any(
                keyword.arg == "shell"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in node.keywords
            )
            if shell_true:
                findings.append((
                    "ERROR", relative, node.lineno,
                    "subprocess is called with shell=True; avoid shell parsing for untrusted input",
                ))
        elif name in {"hashlib.md5", "hashlib.sha1"}:
            findings.append((
                "REVIEW", relative, node.lineno,
                "MD5/SHA-1 is unsuitable for security-sensitive hashing; use SHA-256 or stronger",
            ))
        elif name.endswith(".execute") and node.args:
            query = node.args[0]
            if isinstance(query, (ast.JoinedStr, ast.BinOp, ast.Call)):
                findings.append((
                    "REVIEW", relative, node.lineno,
                    "SQL query may be built dynamically; use parameterized queries",
                ))
    return findings


def check_security_code(path: Path) -> None:
    """Scan source files for common risky coding patterns without executing them."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    findings: list[tuple[str, str, int, str]] = []
    scanned = 0
    for current, directories, filenames in os.walk(root):
        directories[:] = [name for name in directories if name not in IGNORED_DIRS]
        for filename in filenames:
            file_path = Path(current) / filename
            if file_path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            try:
                if file_path.stat().st_size > MAX_FILE_BYTES:
                    continue
                source = file_path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            scanned += 1
            relative = file_path.relative_to(root).as_posix()
            if file_path.suffix.lower() == ".py":
                findings.extend(_python_findings(source, relative))
            else:
                for severity, pattern, message in JS_RULES:
                    for match in pattern.finditer(source):
                        line = source.count("\n", 0, match.start()) + 1
                        findings.append((severity, relative, line, message))
            if scanned >= MAX_FILES:
                findings.append((
                    "INFO", "Project scan", 0,
                    f"Stopped at the {MAX_FILES}-file safety limit",
                ))
                break
        if scanned >= MAX_FILES:
            break

    table = Table(title=f"DevAid Code Security Doctor — {root.name}")
    table.add_column("Severity")
    table.add_column("File", style="cyan")
    table.add_column("Line", justify="right")
    table.add_column("Finding")
    styles = {"ERROR": "red", "REVIEW": "yellow", "INFO": "blue"}
    for severity, filename, line, message in findings:
        table.add_row(
            f"[{styles[severity]}]{severity}[/{styles[severity]}]",
            filename,
            str(line or "—"),
            message,
        )
    if not findings:
        table.add_row("[green]PASS[/green]", "—", "—", "No configured risky patterns detected")
    console.print(table)
    errors = sum(item[0] == "ERROR" for item in findings)
    reviews = sum(item[0] == "REVIEW" for item in findings)
    infos = sum(item[0] == "INFO" for item in findings)
    console.print(Panel(
        (
            f"{scanned} source files scanned • {errors} high-risk patterns • "
            f"{reviews} items to review • {infos} informational"
        ),
        title="Code security summary", border_style="cyan",
    ))
    console.print(
        "[dim]Read-only local heuristics. Source is never executed or uploaded. "
        "False positives and missed issues are possible; this is not a substitute "
        "for expert review or a dedicated SAST tool.[/dim]"
    )
