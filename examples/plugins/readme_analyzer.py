"""Example third-party DevAid analyzer plugin."""
from pathlib import Path

from devaid.plugin_sdk import AnalyzerFinding, AnalyzerResult


def analyze(path: Path) -> AnalyzerResult:
    """Return a sample finding without changing the inspected project."""
    readme = path / "README.md"
    if readme.is_file():
        return AnalyzerResult(summary="README found")
    return AnalyzerResult(
        findings=(
            AnalyzerFinding(
                rule_id="example.readme-missing",
                severity="info",
                message="Consider adding a README for project users.",
            ),
        ),
        summary="README missing",
    )
