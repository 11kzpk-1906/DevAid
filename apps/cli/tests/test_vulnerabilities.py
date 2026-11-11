"""Tests for the OSV dependency vulnerability scanner."""
import json
from pathlib import Path
from devaid.diagnostics.vulnerabilities import Dependency, discover_dependencies, scan_vulnerabilities
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()

def test_reads_pinned_requirements(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\nflask>=3\n", encoding="utf-8")
    assert discover_dependencies(tmp_path) == [Dependency("requests", "2.31.0", "PyPI")]

def test_reads_node_lock(tmp_path: Path) -> None:
    data = {"packages": {"": {}, "node_modules/lodash": {"version": "4.17.20"}}}
    (tmp_path / "package-lock.json").write_text(json.dumps(data), encoding="utf-8")
    assert discover_dependencies(tmp_path) == [Dependency("lodash", "4.17.20", "npm")]

def test_offline_never_queries_osv(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    def fail(_dependency):
        raise AssertionError("offline mode attempted network access")
    monkeypatch.setattr("devaid.diagnostics.vulnerabilities.query_osv", fail)
    report = scan_vulnerabilities(tmp_path, offline=True)
    assert report["mode"] == "offline" and report["checked"] == 0
    assert "not checked" in report["notice"]

def test_reports_vulnerability_and_fixed_version(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.19.0\n", encoding="utf-8")
    advisory = {"id": "GHSA-test", "database_specific": {"severity": "HIGH"},
                "affected": [{"ranges": [{"events": [{"introduced": "0"}, {"fixed": "2.20.0"}]}]}]}
    monkeypatch.setattr("devaid.diagnostics.vulnerabilities.query_osv", lambda _dep: [advisory])
    report = scan_vulnerabilities(tmp_path)
    assert report["checked"] == 1
    assert report["findings"][0]["id"] == "GHSA-test"
    assert report["findings"][0]["fixed_versions"] == "2.20.0"

def test_partial_timeout_is_reported(tmp_path: Path, monkeypatch) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\nflask==3.0.0\n", encoding="utf-8")
    def query(dep):
        if dep.name == "requests":
            raise TimeoutError("timed out")
        return []
    monkeypatch.setattr("devaid.diagnostics.vulnerabilities.query_osv", query)
    report = scan_vulnerabilities(tmp_path)
    assert report["checked"] == 1 and len(report["errors"]) == 1

def test_vuln_cli_offline_json(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("requests==2.31.0\n", encoding="utf-8")
    result = runner.invoke(app, ["vuln", str(tmp_path), "--offline", "--format", "json"])
    assert result.exit_code == 0 and '"mode": "offline"' in result.output

def test_vuln_cli_rejects_bad_format(tmp_path: Path) -> None:
    result = runner.invoke(app, ["vuln", str(tmp_path), "--format", "xml"])
    assert result.exit_code == 2
