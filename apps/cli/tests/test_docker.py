"""Tests for the offline Docker Doctor."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_docker_doctor_reports_common_dockerfile_and_compose_issues(
    tmp_path: Path,
) -> None:
    (tmp_path / "Dockerfile").write_text(
        "FROM python:latest\nCOPY . /app\nRUN apt-get install -y curl\n",
        encoding="utf-8",
    )
    (tmp_path / "compose.yaml").write_text(
        "services:\n  app:\n    image: demo:latest\n    privileged: true\n"
        "    environment:\n      API_KEY: replace-me\n",
        encoding="utf-8",
    )

    result = runner.invoke(app, ["docker-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "Docker Doctor" in result.output
    assert "Pin base images" in result.output
    assert "USER" in result.output
    assert "HEALTHCHECK" in result.output
    assert "privileged: true" in result.output
    assert "latest image tag" in result.output
    assert "inline secret assignment" in result.output
    assert "apt-get update" in result.output
    assert "items to review" in result.output


def test_docker_doctor_reports_clean_configuration(tmp_path: Path) -> None:
    (tmp_path / "Dockerfile").write_text(
        "FROM python:3.12-slim\nUSER app\nHEALTHCHECK CMD true\n",
        encoding="utf-8",
    )
    (tmp_path / ".dockerignore").write_text(".git\n.venv\n", encoding="utf-8")
    (tmp_path / "docker-compose.yml").write_text(
        "services:\n  app:\n    image: demo:1.2.0\n", encoding="utf-8"
    )

    result = runner.invoke(app, ["docker-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "0 items to review" in " ".join(result.output.split())


def test_docker_doctor_handles_missing_configuration(tmp_path: Path) -> None:
    result = runner.invoke(app, ["docker-doctor", str(tmp_path)])

    assert result.exit_code == 0
    assert "No Dockerfile or Docker Compose configuration" in result.output


def test_docker_doctor_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["docker-doctor", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
