# ruff: noqa: E501
"""Local-first roadmap diagnostics: SBOM, secrets, SARIF, licenses, Git, coverage, history and explorer."""
from __future__ import annotations

import hashlib
import json
import os
import sys
import re
import subprocess
import tomllib
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import typer
from rich.console import Console
from rich.table import Table
from rich.prompt import Prompt

console = Console()
SKIP_DIRS = {".git", ".venv", "venv", "node_modules", "__pycache__", "dist", "build", ".tox"}
MAX_FILE_BYTES = 1_000_000
MAX_FILES = 5_000
SECRET_PATTERNS = [
    ("aws-access-key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("github-token", re.compile(r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b")),
    ("private-key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("generic-api-key", re.compile(r"(?i)\b(?:api[_-]?key|access[_-]?token|client[_-]?secret)\s*[:=]\s*['\"]?([A-Za-z0-9_./+\-=]{16,})")),
]
SPDX_KNOWN = {"MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause", "ISC", "GPL-2.0-only", "GPL-3.0-only", "LGPL-2.1-only", "MPL-2.0", "Unlicense"}


def _files(root: Path):
    count = 0
    for current, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS and not d.startswith(".devaid"))
        for name in sorted(names):
            path = Path(current) / name
            try:
                if path.is_file() and path.stat().st_size <= MAX_FILE_BYTES:
                    count += 1
                    if count > MAX_FILES:
                        return
                    yield path
            except OSError:
                continue


def _manifest_packages(root: Path) -> list[dict[str, Any]]:
    packages: dict[tuple[str, str, str], dict[str, Any]] = {}
    pyproject = root / "pyproject.toml"
    if pyproject.is_file():
        try:
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            project = data.get("project", {})
            for raw in project.get("dependencies", []):
                match = re.match(r"\s*([A-Za-z0-9_.-]+)\s*(.*)", raw)
                name, version = match.groups() if match else (raw, "")
                packages[(name.lower(), version.strip(), "pypi")] = {"name": name, "version": version.strip() or "unknown", "ecosystem": "pypi", "license": "unknown"}
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            pass
    req = root / "requirements.txt"
    if req.is_file():
        try:
            for line in req.read_text(encoding="utf-8").splitlines():
                match = re.match(r"\s*([A-Za-z0-9_.-]+)(?:==([^;\s]+))?", line)
                if match and not line.lstrip().startswith("#"):
                    name, version = match.groups()
                    packages[(name.lower(), version or "unknown", "pypi")] = {"name": name, "version": version or "unknown", "ecosystem": "pypi", "license": "unknown"}
        except OSError:
            pass
    package = root / "package.json"
    if package.is_file():
        try:
            data = json.loads(package.read_text(encoding="utf-8"))
            for group in ("dependencies", "devDependencies", "optionalDependencies"):
                for name, version in data.get(group, {}).items():
                    packages[(name.lower(), version, "npm")] = {"name": name, "version": version, "ecosystem": "npm", "license": "unknown"}
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
    poetry_lock = root / "poetry.lock"
    if poetry_lock.is_file():
        try:
            poetry_data = tomllib.loads(poetry_lock.read_text(encoding="utf-8"))
            for package in poetry_data.get("package", []):
                package_name = package.get("name")
                version = package.get("version", "unknown")
                license_value = package.get("license", "unknown")
                license_id = (
                    license_value
                    if isinstance(license_value, str) and license_value in SPDX_KNOWN
                    else "unknown"
                )
                if package_name:
                    packages[(package_name.lower(), version, "pypi")] = {
                        "name": package_name,
                        "version": version,
                        "ecosystem": "pypi",
                        "license": license_id,
                    }
        except (OSError, ValueError, tomllib.TOMLDecodeError):
            pass
    lockfile = root / "package-lock.json"
    if lockfile.is_file():
        try:
            lock_data = json.loads(lockfile.read_text(encoding="utf-8"))
            for package_path, metadata in lock_data.get("packages", {}).items():
                if not package_path or not isinstance(metadata, dict):
                    continue
                package_name = metadata.get("name") or package_path.rsplit("node_modules/", 1)[-1]
                version = metadata.get("version", "unknown")
                declared_license = metadata.get("license", "unknown")
                license_id = (
                    declared_license
                    if isinstance(declared_license, str) and declared_license in SPDX_KNOWN
                    else "unknown"
                )
                packages[(package_name.lower(), version, "npm")] = {
                    "name": package_name,
                    "version": version,
                    "ecosystem": "npm",
                    "license": license_id,
                }
        except (OSError, json.JSONDecodeError, AttributeError):
            pass
    return sorted(packages.values(), key=lambda p: (p["ecosystem"], p["name"].lower()))


def generate_sbom(path: Path, output: Path, fmt: str, overwrite: bool = False) -> dict[str, Any]:
    root = path.resolve()
    if not root.is_dir():
        raise ValueError("project path must be an existing directory")
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {output}; pass --overwrite")
    packages = _manifest_packages(root)
    if fmt == "cyclonedx":
        now = datetime.now(UTC).isoformat().replace("+00:00", "Z")
        doc = {"bomFormat": "CycloneDX", "specVersion": "1.5", "version": 1,
               "metadata": {"timestamp": now, "tools": [{"vendor": "DevAid", "name": "devaid"}]},
               "components": [{"type": "library", "name": p["name"], "version": p["version"],
                               "purl": f"pkg:{p['ecosystem']}/{p['name']}@{p['version']}",
                               "licenses": ([{"license": {"id": p["license"]}}] if p["license"] in SPDX_KNOWN else [])} for p in packages]}
    else:
        doc = {"spdxVersion": "SPDX-2.3", "dataLicense": "CC0-1.0",
               "SPDXID": "SPDXRef-DOCUMENT", "name": root.name,
               "documentNamespace": f"https://devaid.local/spdx/{hashlib.sha256(str(root).encode()).hexdigest()}",
               "creationInfo": {"creators": ["Tool: DevAid"], "created": datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")},
               "packages": [{"name": p["name"], "SPDXID": f"SPDXRef-Package-{i}",
                             "versionInfo": p["version"], "downloadLocation": "NOASSERTION",
                             "filesAnalyzed": False, "licenseConcluded": "NOASSERTION",
                             "licenseDeclared": p["license"] if p["license"] in SPDX_KNOWN else "NOASSERTION"} for i, p in enumerate(packages, 1)]}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(doc, indent=2) + "\n", encoding="utf-8")
    return {"format": fmt, "packages": len(packages), "output": str(output)}


def scan_secrets(path: Path) -> list[dict[str, Any]]:
    root = path.resolve()
    if not root.is_dir():
        raise ValueError("project path must be an existing directory")
    results = []
    for file in _files(root):
        if file.name.lower() in {".env.example", ".env.sample", ".env.template"}:
            continue
        try:
            text = file.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for detector, pattern in SECRET_PATTERNS:
                if pattern.search(line):
                    results.append({"ruleId": detector, "path": file.relative_to(root).as_posix(),
                                    "line": line_no, "confidence": "high" if detector != "generic-api-key" else "medium",
                                    "message": "Potential credential detected; value redacted. Rotate it if genuine."})
                    break
    return results


def build_sarif(findings: list[dict[str, Any]]) -> dict[str, Any]:
    rules = sorted({f["ruleId"] for f in findings})
    return {"$schema": "https://json.schemastore.org/sarif-2.1.0.json", "version": "2.1.0",
            "runs": [{"tool": {"driver": {"name": "DevAid", "informationUri": "https://github.com/11kzpk-1906/DevAid",
                               "rules": [{"id": r, "shortDescription": {"text": r.replace("-", " ").title()}} for r in rules]}},
                     "results": [{"ruleId": f["ruleId"], "level": "warning",
                                  "message": {"text": f["message"]},
                                  "locations": [{"physicalLocation": {"artifactLocation": {"uri": f["path"]},
                                      "region": {"startLine": f["line"]}}}]} for f in findings]}]}


def license_inventory(path: Path) -> dict[str, Any]:
    root = path.resolve()
    packages = _manifest_packages(root)
    # Manifest package declarations rarely carry per-dependency license metadata.
    known = sum(p.get("license") in SPDX_KNOWN for p in packages)
    return {
        "packages": [
            {
                "name": p["name"],
                "version": p["version"],
                "ecosystem": p["ecosystem"],
                "license": p.get("license", "unknown"),
                "status": "known" if p.get("license") in SPDX_KNOWN else "unknown",
            }
            for p in packages
        ],
        "summary": {"total": len(packages), "known": known, "unknown": len(packages) - known},
        "notice": "Only verified SPDX identifiers from supported lockfile metadata are shown; this is not legal advice.",
    }


def git_review(path: Path, staged_only: bool = False) -> dict[str, Any]:
    root = path.resolve()
    if not root.is_dir():
        raise ValueError("project path must be an existing directory")

    def run(args: list[str]) -> str:
        result = subprocess.run(
            ["git", "-C", str(root), *args],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode:
            raise ValueError(result.stderr.strip() or "Git command failed")
        return result.stdout

    if not (root / ".git").exists():
        raise ValueError("path is not a Git working tree")

    staged = run(["diff", "--cached", "--name-status", "--find-renames"])
    unstaged = "" if staged_only else run(["diff", "--name-status", "--find-renames"])
    status = run(["status", "--porcelain=v1", "--untracked-files=all"])
    rows: list[dict[str, Any]] = []
    for label, diff_text in (("staged", staged), ("unstaged", unstaged)):
        for line in diff_text.splitlines():
            parts = line.split("\t")
            if len(parts) < 2:
                continue
            filename = parts[-1].split(" -> ")[-1]
            risks = []
            lowered = filename.lower()
            if Path(lowered).name in {".env", "id_rsa", "id_ed25519"} or lowered.endswith((".pem", ".key")):
                risks.append("sensitive-file")
            if any(part in lowered for part in ("dist/", "build/", "coverage/")):
                risks.append("generated-file")
            rows.append({"area": label, "status": parts[0], "path": filename, "risks": risks})

    for line in status.splitlines():
        code = line[:2]
        raw_path = line[3:] if len(line) > 3 else ""
        filename = raw_path.split(" -> ")[-1]
        if code == "??":
            risks = ["untracked"]
            lowered = filename.lower()
            if Path(lowered).name in {".env", "id_rsa", "id_ed25519"} or lowered.endswith((".pem", ".key")):
                risks.append("sensitive-file")
            rows.append({"area": "untracked", "status": code, "path": filename, "risks": risks})

    added_secret_lines = 0
    diff_args = ["diff", "--cached", "--unified=0"] if staged_only else [
        "diff", "--cached", "--unified=0"
    ]
    if not staged_only:
        diff_args.extend(["--no-ext-diff"])
    diff_text = run(diff_args)
    if not staged_only:
        diff_text += run(["diff", "--unified=0", "--no-ext-diff"])
    for changed_line in diff_text.splitlines():
        if changed_line.startswith("+") and not changed_line.startswith("+++"):
            if any(pattern.search(changed_line) for _, pattern in SECRET_PATTERNS):
                added_secret_lines += 1
    return {
        "changes": rows,
        "working_tree_status": status.splitlines(),
        "potential_secret_lines_added": added_secret_lines,
        "summary": {
            "staged": sum(row["area"] == "staged" for row in rows),
            "unstaged": sum(row["area"] == "unstaged" for row in rows),
            "untracked": sum(row["area"] == "untracked" for row in rows),
        },
        "read_only": True,
    }


def coverage_report(path: Path) -> dict[str, Any]:
    root = path.resolve()
    candidates = [root / "coverage.json", root / "coverage" / "coverage.json"]
    for candidate in candidates:
        if candidate.is_file():
            try:
                data = json.loads(candidate.read_text(encoding="utf-8"))
                totals = data.get("totals", {})
                age_days = (datetime.now(UTC).timestamp() - candidate.stat().st_mtime) / 86400
                return {"source": str(candidate.relative_to(root)), "available": True,
                        "stale": age_days > 180, "age_days": round(age_days),
                        "covered_lines": totals.get("covered_lines"), "total_lines": totals.get("num_statements"),
                        "percent": totals.get("percent_covered"), "files": len(data.get("files", {}))}
            except (OSError, json.JSONDecodeError, AttributeError):
                return {"available": False, "error": f"Malformed coverage report: {candidate.name}"}
    xml_path = root / "coverage.xml"
    if xml_path.is_file():
        try:
            xml = ET.parse(xml_path).getroot()
            age_days = (datetime.now(UTC).timestamp() - xml_path.stat().st_mtime) / 86400
            return {"source": "coverage.xml", "available": True, "stale": age_days > 180,
                    "age_days": round(age_days),
                    "percent": float(xml.attrib.get("line-rate", "0")) * 100,
                    "files": len(xml.findall(".//class"))}
        except (OSError, ET.ParseError, ValueError):
            return {"available": False, "error": "Malformed coverage.xml"}
    return {"available": False, "message": "No coverage report found. Run your test tool with coverage enabled, then retry."}


def save_history(path: Path, output: Path, overwrite: bool = False) -> dict[str, Any]:
    root = path.resolve()
    if not root.is_dir():
        raise ValueError("project path must be an existing directory")
    if output.exists() and not overwrite:
        raise FileExistsError(f"refusing to overwrite {output}; pass --overwrite")
    files = list(_files(root))
    secret_findings = scan_secrets(root)
    summary = {
        "schemaVersion": 1,
        "timestamp": datetime.now(UTC).isoformat(),
        "devaidVersion": "0.3.0",
        "profile": "basic-local",
        "metrics": {
            "filesScanned": len(files),
            "pythonFiles": sum(p.suffix == ".py" for p in files),
            "testFiles": sum("test" in p.name.lower() for p in files),
            "secretFindings": len(secret_findings),
        },
        "findings": [
            {key: finding[key] for key in ("ruleId", "path", "line", "confidence")}
            for finding in secret_findings
        ],
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return summary


def compare_history(before: Path, after: Path) -> dict[str, Any]:
    a, b = json.loads(before.read_text(encoding="utf-8")), json.loads(after.read_text(encoding="utf-8"))
    if a.get("schemaVersion") != 1 or b.get("schemaVersion") != 1:
        raise ValueError("unsupported history schema version")
    am, bm = a.get("metrics", {}), b.get("metrics", {})
    keys = sorted(set(am) | set(bm))
    return {"before": a.get("timestamp"), "after": b.get("timestamp"),
            "changes": {k: {"before": am.get(k), "after": bm.get(k),
                            "delta": (bm.get(k, 0) - am.get(k, 0)) if isinstance(am.get(k), (int, float)) and isinstance(bm.get(k), (int, float)) else None}
                        for k in keys}}


def explore_project(path: Path, max_depth: int = 2) -> list[str]:
    root = path.resolve()
    if not root.is_dir():
        raise ValueError("project path must be an existing directory")
    lines = [root.name + "/"]
    def visit(folder: Path, prefix: str, depth: int):
        if depth >= max_depth:
            return
        try:
            children = sorted((p for p in folder.iterdir() if p.name not in SKIP_DIRS and not p.name.startswith(".devaid")),
                              key=lambda p: (p.is_file(), p.name.lower()))
        except OSError:
            return
        for index, child in enumerate(children[:200]):
            last = index == len(children[:200]) - 1
            lines.append(prefix + ("└── " if last else "├── ") + child.name + ("/" if child.is_dir() else ""))
            if child.is_dir():
                visit(child, prefix + ("    " if last else "│   "), depth + 1)
    visit(root, "", 0)
    return lines


def sbom_command(path: Path = Path("."), output: Path = Path("sbom.json"),
                 fmt: str = typer.Option("cyclonedx", "--format", help="cyclonedx or spdx"),
                 overwrite: bool = typer.Option(False, "--overwrite")) -> None:
    if fmt not in {"cyclonedx", "spdx"}:
        raise typer.BadParameter("--format must be cyclonedx or spdx")
    try:
        result = generate_sbom(path, output, fmt, overwrite)
    except (OSError, ValueError) as error:
        console.print(f"[red]SBOM failed: {error}[/red]")
        raise typer.Exit(1) from error
    console.print(f"[green]Wrote {fmt} SBOM with {result['packages']} packages to {output}[/green]")


def secrets_command(path: Path = Path("."), output: Path | None = None) -> None:
    try:
        findings = scan_secrets(path)
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error
    result = {"findings": findings, "count": len(findings), "values_redacted": True}
    if output:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    console.print_json(json.dumps(result))


def sarif_command(path: Path = Path("."), output: Path = Path("devaid.sarif")) -> None:
    findings = scan_secrets(path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(build_sarif(findings), indent=2) + "\n", encoding="utf-8")
    console.print(f"[green]SARIF report written to {output} ({len(findings)} findings)[/green]")


def licenses_command(path: Path = Path("."), output: Path | None = None) -> None:
    result = license_inventory(path)
    if output:
        output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    console.print_json(json.dumps(result))


def git_review_command(path: Path = Path("."), staged_only: bool = typer.Option(False, "--staged-only")) -> None:
    try:
        result = git_review(path, staged_only)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        console.print(f"[red]Git review failed: {error}[/red]")
        raise typer.Exit(1) from error
    table = Table(title="DevAid Git change review")
    for heading in ("Area", "Status", "Path", "Risk flags"):
        table.add_column(heading)
    for item in result["changes"]:
        table.add_row(item["area"], item["status"], item["path"], ", ".join(item["risks"]) or "—")
    console.print(table)
    console.print("Read-only: Git state and working-tree files were not modified.")


def coverage_command(path: Path = Path(".")) -> None:
    result = coverage_report(path)
    console.print_json(json.dumps(result))


def history_command(path: Path = Path("."), output: Path = Path(".devaid/history/latest.json"),
                    overwrite: bool = typer.Option(False, "--overwrite")) -> None:
    try:
        result = save_history(path, output, overwrite)
    except (OSError, ValueError) as error:
        console.print(f"[red]History save failed: {error}[/red]")
        raise typer.Exit(1) from error
    console.print(f"[green]Saved local history snapshot to {output}[/green]")
    console.print_json(json.dumps(result))


def history_compare_command(before: Path, after: Path) -> None:
    try:
        console.print_json(json.dumps(compare_history(before, after)))
    except (OSError, ValueError, json.JSONDecodeError) as error:
        console.print(f"[red]History comparison failed: {error}[/red]")
        raise typer.Exit(1) from error


def explorer_command(
    path: Path = Path("."),
    depth: int = typer.Option(2, "--depth", min=1, max=5),
    no_interactive: bool = typer.Option(False, "--no-interactive", help="Print a static tree."),
) -> None:
    try:
        root = path.resolve()
        lines = explore_project(root, depth)
    except ValueError as error:
        console.print(f"[red]{error}[/red]")
        raise typer.Exit(1) from error
    if no_interactive or not sys.stdin.isatty():
        console.print("\\n".join(lines))
        return

    current = root
    while True:
        try:
            children = sorted(
                (item for item in current.iterdir()
                 if item.name not in SKIP_DIRS and not item.name.startswith(".devaid")),
                key=lambda item: (item.is_file(), item.name.lower()),
            )
        except OSError as error:
            console.print(f"[red]Cannot read directory: {error}[/red]")
            return
        console.print(f"\\n[bold cyan]{current.relative_to(root) if current != root else root.name}/[/bold cyan]")
        for index, child in enumerate(children[:200], 1):
            suffix = "/" if child.is_dir() else ""
            console.print(f"  {index:>3}. {child.name}{suffix}")
        console.print("  [dim].. = parent | q = quit[/dim]")
        choice = Prompt.ask("Open entry", default="q")
        if choice.lower() in {"q", "quit"}:
            return
        if choice == "..":
            if current != root:
                current = current.parent
            continue
        if not choice.isdigit() or not 1 <= int(choice) <= min(len(children), 200):
            console.print("[yellow]Choose a listed number, '..', or 'q'.[/yellow]")
            continue
        selected = children[int(choice) - 1]
        if selected.is_dir():
            current = selected
        else:
            console.print(f"[cyan]{selected.relative_to(root)}[/cyan] ({selected.stat().st_size} bytes)")
