import pytest
from devaid.plugin_sdk import (
    PLUGIN_API_VERSION,
    AnalyzerFinding,
    AnalyzerResult,
    parse_plugin_manifest,
    validate_analyzer,
)


def test_plugin_manifest_is_versioned_and_validated() -> None:
    manifest = parse_plugin_manifest(
        '[devaid-plugin]\nname = "demo"\napi-version = 1\n'
        'entry-point = "demo.plugin:analyze"\n'
    )
    assert manifest.name == "demo"
    assert manifest.api_version == PLUGIN_API_VERSION
    with pytest.raises(ValueError, match="unsupported"):
        parse_plugin_manifest(
            '[devaid-plugin]\nname="demo"\napi-version=99\n'
            'entry-point="demo:run"'
        )


def test_plugin_manifest_rejects_malformed_and_missing_entry_point() -> None:
    with pytest.raises(ValueError, match="TOML"):
        parse_plugin_manifest("[devaid-plugin")
    with pytest.raises(ValueError, match="entry-point"):
        parse_plugin_manifest(
            '[devaid-plugin]\nname="demo"\napi-version=1'
        )


def test_analyzer_validation_does_not_execute_plugin() -> None:
    called = False

    def analyzer(path):
        nonlocal called
        called = True
        return AnalyzerResult()

    validate_analyzer(analyzer)
    assert called is False
    with pytest.raises(TypeError):
        validate_analyzer(lambda: None)


def test_result_contract_is_immutable() -> None:
    result = AnalyzerResult(
        findings=(AnalyzerFinding("demo.rule", "warning", "Example"),),
        summary="one finding",
    )
    assert result.findings[0].rule_id == "demo.rule"
