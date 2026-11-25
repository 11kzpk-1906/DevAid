import pytest
from devaid.plugin_sdk import (
    PLUGIN_API_VERSION,
    AnalyzerFinding,
    AnalyzerResult,
    parse_plugin_manifest,
    validate_analyzer,
    validate_entry_point_metadata,
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

def test_entry_point_manifest_is_checked_before_code_loading() -> None:
    class Distribution:
        def read_text(self, filename):
            assert filename == "devaid-plugin.toml"
            return (
                '[devaid-plugin]\\nname="demo"\\napi-version=1\\n'
                'entry-point="demo.plugin:analyze"'
            )

    class EntryPoint:
        name = "demo"
        value = "demo.plugin:analyze"
        dist = Distribution()

    manifest = validate_entry_point_metadata(EntryPoint())
    assert manifest is not None
    assert manifest.entry_point == "demo.plugin:analyze"


def test_entry_point_manifest_mismatch_is_rejected() -> None:
    class Distribution:
        def read_text(self, filename):
            return (
                '[devaid-plugin]\\nname="other"\\napi-version=1\\n'
                'entry-point="demo.plugin:analyze"'
            )

    class EntryPoint:
        name = "demo"
        value = "demo.plugin:analyze"
        dist = Distribution()

    with pytest.raises(ValueError, match="name does not match"):
        validate_entry_point_metadata(EntryPoint())
