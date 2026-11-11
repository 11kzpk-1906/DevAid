import re
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console(width=140)
IGNORED_DIRS = {
    ".git",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".tox",
    "dist",
    "build",
}
COMPOSE_NAME = re.compile(
    r"^(?:compose|docker-compose)(?:\.[^.]+)?\.(?:yml|yaml)$",
    re.IGNORECASE,
)
SECRET_ASSIGNMENT = re.compile(
    r"(?i)^\s*[A-Z0-9_]*(?:PASSWORD|PASSWD|SECRET|TOKEN|API_KEY)[A-Z0-9_]*\s*:"
)


def _project_files(root: Path) -> list[Path]:
    """Return Docker-related files while skipping common generated directories."""
    found: list[Path] = []
    for file_path in root.rglob("*"):
        if not file_path.is_file() or any(
            part in IGNORED_DIRS for part in file_path.relative_to(root).parts
        ):
            continue
        name = file_path.name
        if name == "Dockerfile" or name.startswith("Dockerfile.") or COMPOSE_NAME.match(name):
            found.append(file_path)
    return sorted(found)


def _inspect_dockerfile(file_path: Path, root: Path) -> list[tuple[str, str, str]]:
    relative = file_path.relative_to(root).as_posix()
    findings: list[tuple[str, str, str]] = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return [("REVIEW", relative, "Could not read this Dockerfile")]

    active_lines = [
        line.strip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    from_lines = [line for line in active_lines if re.match(r"^FROM\s+", line, re.I)]
    if not from_lines:
        findings.append(("REVIEW", relative, "No FROM instruction was found"))
    else:
        floating_images: list[str] = []
        for line in from_lines:
            parts = line.split()
            image_index = next(
                (index for index, part in enumerate(parts) if part.upper() == "FROM"),
                -1,
            )
            if image_index < 0 or image_index + 1 >= len(parts):
                continue
            image = parts[image_index + 1]
            if image.startswith("--") and image_index + 2 < len(parts):
                image = parts[image_index + 2]
            if image == "scratch" or "@" in image:
                continue
            last_component = image.rsplit("/", 1)[-1]
            if ":" not in last_component or last_component.endswith(":latest"):
                floating_images.append(image)
        if floating_images:
            findings.append(
                (
                    "REVIEW",
                    relative,
                    "Pin base images to an explicit version or digest instead of latest",
                )
            )
        else:
            findings.append(("PASS", relative, "Base images use explicit tags or digests"))

    if any(re.match(r"^USER\s+\S+", line, re.I) for line in active_lines):
        findings.append(("PASS", relative, "A non-default runtime USER is declared"))
    else:
        findings.append(
            ("REVIEW", relative, "Consider adding USER to avoid running as root")
        )

    if any(re.match(r"^HEALTHCHECK\s+", line, re.I) for line in active_lines):
        findings.append(("PASS", relative, "A HEALTHCHECK instruction is present"))
    else:
        findings.append(
            ("REVIEW", relative, "Consider adding a HEALTHCHECK for runtime monitoring")
        )

    if any(re.match(r"^ADD\s+", line, re.I) for line in active_lines):
        findings.append(
            ("REVIEW", relative, "Review ADD usage; prefer COPY unless ADD features are needed")
        )

    broad_copy = any(
        re.match(r"^COPY\s+(?:--[^ ]+\s+)*[.](?:\s|$)", line, re.I)
        for line in active_lines
    )
    if broad_copy and not (root / ".dockerignore").is_file():
        findings.append(
            ("REVIEW", relative, "Broad COPY detected but the project has no .dockerignore")
        )

    if any(re.search(r"apt-get\s+install", line, re.I) for line in active_lines) and not any(
        re.search(r"apt-get\s+update", line, re.I) for line in active_lines
    ):
        findings.append(
            ("REVIEW", relative, "apt-get install found without apt-get update")
        )

    if not findings:
        findings.append(("INFO", relative, "No common Dockerfile patterns were detected"))
    return findings


def _inspect_compose(file_path: Path, root: Path) -> list[tuple[str, str, str]]:
    relative = file_path.relative_to(root).as_posix()
    findings: list[tuple[str, str, str]] = []
    try:
        lines = file_path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return [("REVIEW", relative, "Could not read this Compose file")]

    active_lines = [
        line.rstrip()
        for line in lines
        if line.strip() and not line.lstrip().startswith("#")
    ]
    for line in active_lines:
        stripped = line.strip()
        if re.match(r"(?i)^privileged\s*:\s*true\b", stripped):
            findings.append(
                ("REVIEW", relative, "privileged: true grants the container elevated host access")
            )
            break
    else:
        findings.append(("PASS", relative, "No privileged: true setting was detected"))

    if any(
        re.search(r"(?i)\bimage\s*:\s*[^\s#]+:latest\b", line)
        for line in active_lines
    ):
        findings.append(("REVIEW", relative, "An image uses the mutable latest tag"))
    else:
        findings.append(("PASS", relative, "No explicit latest image tag was detected"))

    secret_lines = [
        line for line in active_lines if SECRET_ASSIGNMENT.match(line.strip())
    ]
    if secret_lines:
        findings.append(
            (
                "REVIEW",
                relative,
                f"{len(secret_lines)} possible inline secret assignment(s); use environment "
                "variables or a secrets manager and never commit real credentials",
            )
        )
    else:
        findings.append(("PASS", relative, "No obvious inline secret assignments were detected"))

    return findings


def docker_doctor(path: Path) -> None:
    """Inspect local Dockerfiles and Compose files without running Docker."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    root = path.resolve()
    files = _project_files(root)
    if not files:
        console.print(
            "[yellow]No Dockerfile or Docker Compose configuration was found.[/yellow]"
        )
        return

    findings: list[tuple[str, str, str]] = []
    for file_path in files:
        name = file_path.name
        if name == "Dockerfile" or name.startswith("Dockerfile."):
            findings.extend(_inspect_dockerfile(file_path, root))
        else:
            findings.extend(_inspect_compose(file_path, root))

    table = Table(title=f"DevAid Docker Doctor — {root.name}")
    table.add_column("Status")
    table.add_column("File", style="cyan")
    table.add_column("Finding")
    styles = {"PASS": "green", "REVIEW": "yellow", "INFO": "blue"}
    for status, filename, details in findings:
        style = styles[status]
        table.add_row(f"[{style}]{status}[/{style}]", filename, details)
    console.print(table)

    passed = sum(item[0] == "PASS" for item in findings)
    review = sum(item[0] == "REVIEW" for item in findings)
    info = sum(item[0] == "INFO" for item in findings)
    console.print(
        Panel(
            f"{len(files)} Docker configuration files checked • {passed} passed • "
            f"{review} items to review • {info} informational",
            title="Docker hygiene summary",
            border_style="cyan",
        )
    )
    console.print(
        f"Summary: {len(files)} files checked; {passed} passed; "
        f"{review} items to review; {info} informational"
    )
    console.print(
        "[dim]Local, read-only heuristic checks. DevAid does not build or run containers, "
        "change files, or upload project data. Verify each recommendation for your setup.[/dim]"
    )
