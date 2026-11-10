from pathlib import Path

from scripts.check_markdown_links import check_file


def test_valid_relative_link_and_anchor(tmp_path: Path) -> None:
    docs = tmp_path / "docs"
    docs.mkdir()
    target = docs / "guide.md"
    target.write_text("# Getting Started\n", encoding="utf-8")
    source = docs / "index.md"
    source.write_text("[Guide](guide.md# getting-started)".replace("# ", "#"), encoding="utf-8")

    assert check_file(source) == []


def test_reports_missing_local_file(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text("[Missing](docs/missing.md)\n", encoding="utf-8")

    errors = check_file(source)

    assert len(errors) == 1
    assert "broken local link" in errors[0]


def test_reports_missing_heading_anchor(tmp_path: Path) -> None:
    target = tmp_path / "guide.md"
    target.write_text("# Existing Section\n", encoding="utf-8")
    source = tmp_path / "README.md"
    source.write_text("[Guide](guide.md#missing-section)\n", encoding="utf-8")

    errors = check_file(source)

    assert len(errors) == 1
    assert "missing anchor" in errors[0]


def test_ignores_external_links_and_code_examples(tmp_path: Path) -> None:
    source = tmp_path / "README.md"
    source.write_text(
        "[External](https://example.com)\n\n```md\n[Fake](missing.md)\n```\n",
        encoding="utf-8",
    )

    assert check_file(source) == []


def test_supports_reference_style_links(tmp_path: Path) -> None:
    target = tmp_path / "guide.md"
    target.write_text("# Guide\n", encoding="utf-8")
    source = tmp_path / "README.md"
    source.write_text("[Guide][docs]\n\n[docs]: guide.md\n", encoding="utf-8")

    assert check_file(source) == []
