"""Opt-in dependency vulnerability checks using OSV.dev."""
from __future__ import annotations
import json
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

OSV_QUERY_URL = "https://api.osv.dev/v1/query"
_PINNED = re.compile(r"^([A-Za-z0-9][A-Za-z0-9._-]*)\\s*==\\s*([A-Za-z0-9][A-Za-z0-9.+!_-]*)")

@dataclass(frozen=True, order=True)
class Dependency:
    name: str
    version: str
    ecosystem: str

def _requirements(path: Path) -> list[Dependency]:
    found = set()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _PINNED.match(line.strip())
        if match:
            found.add(Dependency(match.group(1), match.group(2), "PyPI"))
    return sorted(found)

def _toml_lock(path: Path) -> list[Dependency]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    return sorted({Dependency(str(item["name"]), str(item["version"]), "PyPI") for item in data.get("package", []) if item.get("name") and item.get("version")})

def _node_lock(path: Path) -> list[Dependency]:
    data = json.loads(path.read_text(encoding="utf-8"))
    return sorted({Dependency(key.rsplit("node_modules/", 1)[-1], str(value["version"]), "npm") for key, value in data.get("packages", {}).items() if key.startswith("node_modules/") and isinstance(value, dict) and value.get("version")})

def discover_dependencies(path: Path) -> list[Dependency]:
    """Read exact versions from supported lockfiles and pinned requirements."""
    result = set()
    readers = (("uv.lock", _toml_lock), ("poetry.lock", _toml_lock), ("requirements.txt", _requirements), ("package-lock.json", _node_lock), ("npm-shrinkwrap.json", _node_lock))
    for filename, reader in readers:
        manifest = path / filename
        if manifest.is_file():
            try:
                result.update(reader(manifest))
            except (OSError, ValueError, TypeError, KeyError, tomllib.TOMLDecodeError):
                continue
    return sorted(result)

def query_osv(dependency: Dependency) -> list[dict[str, object]]:
    """Send package coordinates only; never send project files."""
    payload = {"package": {"name": dependency.name, "ecosystem": dependency.ecosystem}, "version": dependency.version}
    request = Request(OSV_QUERY_URL, data=json.dumps(payload).encode(), headers={"Content-Type": "application/json", "User-Agent": "DevAid"}, method="POST")
    with urlopen(request, timeout=8) as response:
        body = json.loads(response.read().decode("utf-8"))
    vulns = body.get("vulns", [])
    if not isinstance(vulns, list):
        raise ValueError("Invalid OSV vulnerabilities response")
    return [item for item in vulns if isinstance(item, dict)]

def scan_vulnerabilities(path: Path, offline: bool = False) -> dict[str, object]:
    """Scan pinned dependencies; offline mode never contacts OSV."""
    report: dict[str, object] = {"project": path.resolve().name, "mode": "offline" if offline else "online", "checked": 0, "findings": [], "errors": [], "notice": "Offline mode: current OSV advisories were not checked." if offline else "Only package names, versions, and ecosystems are sent to OSV.dev."}
    if offline:
        return report
    findings = []
    errors = []
    for dep in discover_dependencies(path):
        try:
            for item in query_osv(dep):
                fixed = set()
                for affected in item.get("affected", []):
                    for version_range in affected.get("ranges", []):
                        fixed.update(str(event["fixed"]) for event in version_range.get("events", []) if event.get("fixed"))
                database = item.get("database_specific", {})
                findings.append({"package": dep.name, "version": dep.version, "ecosystem": dep.ecosystem, "id": str(item.get("id", "Unknown")), "summary": str(item.get("summary", "")), "severity": str(database.get("severity", "Unknown")) if isinstance(database, dict) else "Unknown", "fixed_versions": ", ".join(sorted(fixed)) or "Not listed"})
            report["checked"] = int(report["checked"]) + 1
        except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
            errors.append(f"{dep.ecosystem}:{dep.name}@{dep.version}: {error}")
    report["findings"] = sorted(findings, key=lambda item: (str(item["package"]).casefold(), str(item["id"])))
    report["errors"] = errors
    return report