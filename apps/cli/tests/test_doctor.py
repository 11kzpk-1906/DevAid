"""Tests for the combined Full Doctor command."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_full_doctor_runs_all_local_checks(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Sample\n\n## Installation\n\n## Usage\n\n## Contributing\n\n## License\n",
        encoding="utf-8",
    )
    (tmp_path / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.12-slim\nUSER app\nHEALTHCHECK CMD true\n",
        encoding="utf-8",
    )
    workflow_dir = tmp_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True)
    (workflow_dir / "ci.yml").write_text(
        "name: CI\npermissions:\n  contents: read\n", encoding="utf-8"
    )
    (tmp_path / "pyproject.toml").write_text(
        '[project]\nname = "sample"\nversion = "1.0.0"\n',
        encoding="utf-8",
    )

    result = runner.invoke(app, ["doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "DevAid Full Doctor" in result.output
    assert "Project Health" in result.output
    assert "Dependency Doctor" in result.output
    assert "Config Doctor" in result.output
    assert "Deployment Doctor" in result.output
    assert "Documentation Doctor" in result.output
    assert "Security Doctor" in result.output
    assert "Environment Doctor" in result.output
    assert "Git Doctor" in result.output
    assert "Release Doctor" in result.output
    assert "Performance Doctor" in result.output
    assert "Accessibility Doctor" in result.output
    assert "Workflow Doctor" in result.output
    assert "Docker Doctor" in result.output
    assert "Package Manager Doctor" in result.output
    assert "Python Doctor" in result.output
    assert "JavaScript Doctor" in result.output
    assert "Full Doctor complete" in result.output
    assert "Final summary:" in result.output
    assert "17/17 diagnostic reports completed" in " ".join(result.output.split())


def test_full_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["doctor", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
