"""Tests for the offline Security Doctor command."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_security_detects_credentials_without_printing_values(tmp_path: Path) -> None:
    sample_value = "sk_live_" + "abcdefghijklmnop"
    key_name = "api_" + "key"
    (tmp_path / ".gitignore").write_text(".env\n.env.*\n", encoding="utf-8")
    source = f'{key_name} = "{sample_value}"\nprint("hello")\n'
    (tmp_path / "app.py").write_text(source, encoding="utf-8")

    result = runner.invoke(app, ["security", str(tmp_path)])

    assert result.exit_code == 0
    assert "Security Doctor" in result.output
    assert "Credential assignment" in result.output
    assert sample_value not in result.output
    assert "1 potential risks" in " ".join(result.output.split())


def test_security_reports_env_file_and_missing_ignore_rule(tmp_path: Path) -> None:
    env_line = "PASS" + "WORD" + "=" + "not-for-output" + "\n"
    (tmp_path / ".env").write_text(env_line, encoding="utf-8")
    (tmp_path / "app.py").write_text("print('safe')\n", encoding="utf-8")

    result = runner.invoke(app, ["security", str(tmp_path)])

    assert result.exit_code == 0
    assert "Environment file exists" in result.output
    assert "Add .env and .env.* to .gitignore" in result.output
    assert "not-for-output" not in result.output


def test_security_ignores_common_generated_directories(tmp_path: Path) -> None:
    generated = tmp_path / "node_modules" / "sample"
    generated.mkdir(parents=True)
    sample_value = "sk_live_" + "abcdefghijklmnop"
    key_name = "api_" + "key"
    source = f'const {key_name} = "{sample_value}";\n'
    (generated / "index.js").write_text(source, encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")

    result = runner.invoke(app, ["security", str(tmp_path)])

    assert result.exit_code == 0
    assert "potential risks" in result.output
    assert "node_modules" not in result.output


def test_security_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["security", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output


def test_security_detects_sensitive_files_tracked_by_git(tmp_path: Path) -> None:
    import subprocess

    (tmp_path / ".gitignore").write_text(".env\n", encoding="utf-8")
    (tmp_path / ".env").write_text("TOKEN=redacted-value\n", encoding="utf-8")
    (tmp_path / "private.pem").write_text("placeholder private key\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", "-f", ".env", "private.pem"],
        check=True,
    )

    result = runner.invoke(app, ["security", str(tmp_path)])

    assert result.exit_code == 0
    assert "Sensitive-looking file is tracked by Git" in result.output
    assert ".env" in result.output
    assert "private.pem" in result.output
    assert "redacted-value" not in result.output


def test_security_does_not_flag_env_example_tracked_by_git(tmp_path: Path) -> None:
    import subprocess

    (tmp_path / ".env.example").write_text("API_KEY=your_key_here\n", encoding="utf-8")
    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    subprocess.run(
        ["git", "-C", str(tmp_path), "add", ".env.example"],
        check=True,
    )

    result = runner.invoke(app, ["security", str(tmp_path)])

    assert result.exit_code == 0
    assert "Sensitive-looking file is tracked by Git" not in result.output
