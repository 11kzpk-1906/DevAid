import json
import subprocess
from pathlib import Path
import pytest
from devaid.diagnostics.roadmap import build_sarif, compare_history, coverage_report, explore_project, generate_sbom, git_review, license_inventory, save_history, scan_secrets

def test_sbom_formats_and_overwrite_guard(tmp_path: Path) -> None:
    (tmp_path / "pyproject.toml").write_text('[project]\ndependencies = ["requests>=2"]\n')
    cyclonedx = tmp_path / "bom.json"
    assert generate_sbom(tmp_path, cyclonedx, "cyclonedx")["packages"] == 1
    assert json.loads(cyclonedx.read_text())["bomFormat"] == "CycloneDX"
    with pytest.raises(FileExistsError): generate_sbom(tmp_path, cyclonedx, "spdx")
    spdx = tmp_path / "spdx.json"
    generate_sbom(tmp_path, spdx, "spdx")
    assert json.loads(spdx.read_text())["spdxVersion"] == "SPDX-2.3"

def test_secret_scan_redacts_values_and_skips_examples(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TOKEN=ghp_" + "A" * 30)
    (tmp_path / ".env.example").write_text("TOKEN=ghp_" + "B" * 30)
    (tmp_path / ".gitignore").write_text("ignored/")
    (tmp_path / "ignored").mkdir()
    (tmp_path / "ignored" / "secret.py").write_text("TOKEN=ghp_" + "C" * 30)
    findings = scan_secrets(tmp_path)
    assert len(findings) == 1
    assert "ghp_" not in json.dumps(findings)

def test_sarif_has_locations_and_rules() -> None:
    sarif = build_sarif([{"ruleId":"demo-secret","path":"src/a.py","line":4,"message":"redacted"}])
    assert sarif["version"] == "2.1.0"
    from devaid.diagnostics.roadmap import validate_sarif
    validate_sarif(sarif)
    assert sarif["runs"][0]["results"][0]["locations"][0]["physicalLocation"]["region"]["startLine"] == 4

def test_license_inventory_does_not_guess(tmp_path: Path) -> None:
    (tmp_path / "requirements.txt").write_text("sample-lib==1.2.3\n")
    result = license_inventory(tmp_path)
    assert result["summary"]["unknown"] == 1
    assert result["packages"][0]["license"] == "unknown"
    (tmp_path / "package-lock.json").write_text(json.dumps({"packages": {"": {}, "node_modules/demo": {"name": "demo", "version": "1.0.0", "license": "MIT"}}}))
    enriched = license_inventory(tmp_path)
    assert enriched["summary"]["known"] == 1
    assert enriched["packages"][0]["license"] == "MIT"
    (tmp_path / ".devaid.toml").write_text('[licenses]\ndeny = ["MIT"]\n')
    denied = license_inventory(tmp_path)
    assert denied["summary"]["denied"] == 1

def test_git_review_is_read_only(tmp_path: Path) -> None:
    subprocess.run(["git","init",str(tmp_path)],check=True,capture_output=True)
    subprocess.run(["git","-C",str(tmp_path),"config","user.email","test@example.com"],check=True)
    subprocess.run(["git","-C",str(tmp_path),"config","user.name","Test"],check=True)
    (tmp_path / ".env").write_text("placeholder")
    subprocess.run(["git","-C",str(tmp_path),"add",".env"],check=True)
    before=subprocess.run(["git","-C",str(tmp_path),"status","--short"],check=True,capture_output=True,text=True).stdout
    result=git_review(tmp_path)
    after=subprocess.run(["git","-C",str(tmp_path),"status","--short"],check=True,capture_output=True,text=True).stdout
    assert before == after
    assert result["changes"][0]["risks"] == ["sensitive-file"]
    (tmp_path / "notes.txt").write_text("untracked")
    refreshed = git_review(tmp_path)
    assert refreshed["summary"]["untracked"] == 1

def test_coverage_missing_and_json(tmp_path: Path) -> None:
    assert coverage_report(tmp_path)["available"] is False
    (tmp_path / "coverage.json").write_text(json.dumps({"totals":{"covered_lines":8,"num_statements":10,"percent_covered":80},"files":{"a.py":{}}}))
    assert coverage_report(tmp_path)["percent"] == 80

def test_history_round_trip_and_compare(tmp_path: Path) -> None:
    history_dir=tmp_path/".devaid"/"history"
    before, after=history_dir/"before.json",history_dir/"after.json"
    save_history(tmp_path,before)
    (tmp_path/"module.py").write_text("pass\n")
    save_history(tmp_path,after)
    assert compare_history(before,after)["changes"]["filesScanned"]["delta"] == 1
    with pytest.raises(FileExistsError): save_history(tmp_path,after)

def test_explorer_respects_ignored_directories(tmp_path: Path) -> None:
    (tmp_path/"src").mkdir()
    (tmp_path/"src"/"main.py").write_text("pass")
    (tmp_path/".venv").mkdir()
    lines=explore_project(tmp_path,3)
    assert any("main.py" in line for line in lines)
    assert not any(".venv" in line for line in lines)
