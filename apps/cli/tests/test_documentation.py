"""Tests for the offline Documentation Doctor command."""

from pathlib import Path

from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_docs_reports_complete_documentation(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text(
        "# Demo\n## Installation\n## Usage\n## Contributing\n## License\n",
        encoding="utf-8",
    )
    for filename in (
        "CONTRIBUTING.md",
        "LICENSE",
        "CHANGELOG.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
    ):
        (tmp_path / filename).write_text("Project information", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "guide.md").write_text("# Guide", encoding="utf-8")

    result = runner.invoke(app, ["docs", str(tmp_path)])

    assert result.exit_code == 0
    assert "Documentation Doctor" in result.output
    assert "100/100" in result.output
    assert "10/10 checks passed" in result.output
    assert "does not judge writing quality" in " ".join(result.output.split())


def test_docs_flags_missing_documentation(tmp_path: Path) -> None:
    (tmp_path / "README.md").write_text("# Small project", encoding="utf-8")

    result = runner.invoke(app, ["docs", str(tmp_path)])

    assert result.exit_code == 0
    assert "REVIEW" in result.output
    assert "Documentation score" in result.output


def test_docs_rejects_invalid_directory(tmp_path: Path) -> None:
    result = runner.invoke(app, ["docs", str(tmp_path / "missing")])

    assert result.exit_code == 1
    assert "Invalid project directory" in result.output
