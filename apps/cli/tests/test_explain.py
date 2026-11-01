"""Tests for the Smart Error Analyzer."""

from devaid.commands.explain import _identify_error
from devaid.main import app
from typer.testing import CliRunner

runner = CliRunner()


def test_identifies_exception_from_traceback() -> None:
    error_name, message = _identify_error(
        'Traceback (most recent call last):\n  File "app.py", line 2\n'
        "    print(user.name)\nAttributeError: 'NoneType' object has no attribute 'name'"
    )

    assert error_name == "AttributeError"
    assert "'NoneType'" in message


def test_identifies_supported_error_with_message() -> None:
    error_name, message = _identify_error("ZeroDivisionError: division by zero")

    assert error_name == "ZeroDivisionError"
    assert message == "division by zero"


def test_unknown_error_is_reported_without_crashing() -> None:
    result = runner.invoke(app, ["explain", "CustomFailure: something went wrong"])

    assert result.exit_code == 0
    assert "Unknown Error" in result.output


def test_smart_analyzer_displays_causes_fixes_and_example() -> None:
    result = runner.invoke(app, ["explain", "NameError: name 'total' is not defined"])

    assert result.exit_code == 0
    assert "Likely causes" in result.output
    assert "Recommended next steps" in result.output
    assert "Example" in result.output
    assert "misspelled" in result.output


def test_smart_analyzer_supports_additional_python_errors() -> None:
    result = runner.invoke(app, ["explain", "FileNotFoundError: data.csv"])

    assert result.exit_code == 0
    assert "FileNotFoundError" in result.output
    assert "resolved path" in result.output
