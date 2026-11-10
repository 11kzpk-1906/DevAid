"""Tests for static code security checks."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_security_code_detects_python_risky_patterns(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text(
        "import subprocess\nimport hashlib\n"
        "value = eval(user_input)\n"
        "subprocess.run(command, shell=True)\n"
        "hashlib.md5(data)\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["security-code", str(tmp_path)])
    assert result.exit_code == 0
    assert "eval()" in result.output
    assert "shell=True" in result.output
    assert "MD5/SHA-1" in result.output


def test_security_code_detects_unsafe_yaml_and_pickle(tmp_path: Path) -> None:
    (tmp_path / "sample.py").write_text(
        "import yaml\nimport pickle\nyaml.load(data)\npickle.loads(data)\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["security-code", str(tmp_path)])
    assert result.exit_code == 0
    assert "safe loader" in result.output
    assert "untrusted data" in result.output


def test_security_code_detects_javascript_patterns(tmp_path: Path) -> None:
    (tmp_path / "app.js").write_text(
        "eval(input);\nelement.innerHTML = value;\n"
        "child_process.exec(command);\n",
        encoding="utf-8",
    )
    result = runner.invoke(app, ["security-code", str(tmp_path)])
    assert result.exit_code == 0
    assert "eval()" in result.output
    assert "innerHTML" in result.output
    assert "command injection" in result.output


def test_security_code_ignores_generated_directories(tmp_path: Path) -> None:
    generated = tmp_path / "node_modules"
    generated.mkdir()
    (generated / "bad.js").write_text("eval(input)", encoding="utf-8")
    (tmp_path / "safe.py").write_text("print('safe')", encoding="utf-8")
    result = runner.invoke(app, ["security-code", str(tmp_path)])
    assert result.exit_code == 0
    assert "No configured risky patterns" in result.output


def test_security_code_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["security-code", str(tmp_path / "missing")])
    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
