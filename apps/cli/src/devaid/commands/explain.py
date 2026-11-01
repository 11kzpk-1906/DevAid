"""Rule-based Python error analysis with causes, fixes, and examples."""

import re
from dataclasses import dataclass

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


@dataclass(frozen=True)
class ErrorGuide:
    explanation: str
    causes: tuple[str, ...]
    fixes: tuple[str, ...]
    example: str


ERROR_GUIDES: dict[str, ErrorGuide] = {
    "ModuleNotFoundError": ErrorGuide(
        "Python cannot locate a module requested by an import statement.",
        (
            "The package may not be installed in the active environment.",
            "The import name may differ from the package's installation name.",
            "The project may be running with the wrong Python interpreter.",
        ),
        (
            "Confirm which interpreter runs the project.",
            "Install the dependency in that same environment.",
            "Check the package documentation for its correct import name.",
        ),
        "If the missing module is requests, install it in your project environment "
        "with: uv add requests",
    ),
    "ImportError": ErrorGuide(
        "Python found a module, but it could not import the requested name.",
        (
            "The imported function or class may not exist in that module.",
            "A dependency version may have changed its public API.",
            "A local file may shadow a package with the same name.",
        ),
        (
            "Check the exact name and module path.",
            "Review the installed package version and its documentation.",
            "Look for local files that shadow the imported package.",
        ),
        "For example, verify that the imported name exists: "
        "from package_name import available_name",
    ),
    "SyntaxError": ErrorGuide(
        "Python could not parse the source code.",
        (
            "A colon, bracket, or quotation mark may be missing.",
            "A statement may use invalid Python syntax.",
            "The reported line may be where Python noticed an earlier mistake.",
        ),
        (
            "Open the reported file and inspect the indicated line.",
            "Check the preceding line for an unclosed bracket or quote.",
            "Run the file again after correcting the syntax.",
        ),
        'Example: change "if ready" to "if ready:"',
    ),
    "IndentationError": ErrorGuide(
        "Python found indentation that does not match the block structure.",
        (
            "A block may be missing indentation after a colon.",
            "Tabs and spaces may have been mixed.",
        ),
        (
            "Use consistent four-space indentation.",
            "Align statements inside if, for, while, class, and function blocks.",
        ),
        "if ready:\n    print('Ready')",
    ),
    "NameError": ErrorGuide(
        "Code refers to a name that is not defined in the current scope.",
        (
            "A variable or function name may be misspelled.",
            "The name may be used before it is assigned.",
            "The name may exist only inside another scope.",
        ),
        (
            "Check spelling and capitalization.",
            "Define or import the name before using it.",
            "Check where the name is assigned and whether it is in scope.",
        ),
        "message = 'Hello'\nprint(message)",
    ),
    "TypeError": ErrorGuide(
        "An operation or function received a value of an unsupported type.",
        (
            "Two incompatible types may be used in one operation.",
            "A function may have received the wrong kind or number of arguments.",
            "A value may be None when another type was expected.",
        ),
        (
            "Inspect the types and values passed to the failing operation.",
            "Check the function signature and argument order.",
            "Convert values explicitly only when that matches the intended logic.",
        ),
        "Example: convert input before numeric addition: "
        "total = int(input_value) + 5",
    ),
    "AttributeError": ErrorGuide(
        "An object does not provide the attribute or method being accessed.",
        (
            "The attribute name may be misspelled.",
            "The object may be a different type than expected.",
            "The variable may contain None instead of the expected object.",
        ),
        (
            "Inspect the object's type with type(value).",
            "Check the class or library documentation for the attribute name.",
            "Trace where the variable is assigned, especially if it can be None.",
        ),
        "Example: check a value before accessing its attributes: "
        "if user is not None:\n    print(user.name)",
    ),
    "IndexError": ErrorGuide(
        "A sequence was accessed at a position that does not exist.",
        (
            "The index may be larger than the last valid position.",
            "The list or sequence may be empty.",
        ),
        (
            "Check the sequence length before indexing.",
            "Review loop boundaries and remember that indexes start at zero.",
        ),
        "if items:\n    first_item = items[0]",
    ),
    "KeyError": ErrorGuide(
        "A dictionary lookup requested a key that is not present.",
        (
            "The key may be misspelled or use different capitalization.",
            "The data may not contain the expected field.",
        ),
        (
            "Inspect available keys with dictionary.keys().",
            "Use get() when a missing key is an expected possibility.",
            "Validate incoming data before accessing required fields.",
        ),
        "name = user_data.get('name', 'Unknown')",
    ),
    "ValueError": ErrorGuide(
        "A function received a value of the right general type but an invalid value.",
        (
            "A conversion may have received text that is not a valid number.",
            "A value may be outside the accepted range or format.",
        ),
        (
            "Validate the input before converting or processing it.",
            "Check the function's accepted formats and value ranges.",
        ),
        "Use a try/except ValueError block when parsing user input.",
    ),
    "ZeroDivisionError": ErrorGuide(
        "A division operation attempted to use zero as its divisor.",
        (
            "The denominator may be zero.",
            "A calculated value may unexpectedly become zero.",
        ),
        (
            "Validate the denominator before dividing.",
            "Handle the zero case according to the program's intended behavior.",
        ),
        "if denominator != 0:\n    result = numerator / denominator",
    ),
    "FileNotFoundError": ErrorGuide(
        "Python could not find the file or directory at the supplied path.",
        (
            "The path may be misspelled or relative to a different working directory.",
            "The file may not have been created or may have been moved.",
        ),
        (
            "Print or inspect the resolved path.",
            "Check that the file exists before opening it.",
            "Use pathlib.Path to build paths consistently.",
        ),
        "from pathlib import Path\n\nfile_path = Path('data.txt')\n"
        "if file_path.is_file():\n    text = file_path.read_text()",
    ),
    "PermissionError": ErrorGuide(
        "The operating system denied access to a file or resource.",
        (
            "The current account may not have the required permission.",
            "Another process may be holding the resource.",
        ),
        (
            "Check the file or directory permissions.",
            "Confirm that the application is using the intended path.",
            "Avoid changing permissions broadly; request only the access needed.",
        ),
        "Check access to the specific file before attempting the operation.",
    ),
    "RecursionError": ErrorGuide(
        "A function or operation exceeded Python's recursion limit.",
        (
            "A recursive function may not reach its stopping condition.",
            "The input may create an unexpectedly deep call chain.",
        ),
        (
            "Check that every recursive path moves toward a base case.",
            "Consider an iterative approach for deeply nested work.",
        ),
        "def countdown(n):\n    if n <= 0:\n        return\n"
        "    print(n)\n    countdown(n - 1)",
    ),
}


def _identify_error(error: str) -> tuple[str | None, str]:
    """Identify a supported exception from an error message or traceback."""
    matches = re.findall(r"([A-Za-z][A-Za-z0-9]*(?:Error|Exception))(?::\s*(.*))?", error)
    if not matches:
        return None, error.strip()

    for name, message in reversed(matches):
        if name in ERROR_GUIDES:
            return name, message.strip()
    return matches[-1][0], matches[-1][1].strip()


def explain(error: str = typer.Argument(..., help="The error message or traceback.")) -> None:
    """Explain a Python error with likely causes and practical next steps."""
    error_name, error_message = _identify_error(error)

    if error_name is None or error_name not in ERROR_GUIDES:
        console.print(
            Panel(
                "DevAid could not match this message to a supported Python error.\n"
                "Try pasting the exception name and its message from the traceback.",
                title="Unknown Error",
                border_style="yellow",
            )
        )
        return

    guide = ERROR_GUIDES[error_name]
    title = f"DevAid Smart Error Analyzer · {error_name}"
    console.print(
        Panel(
            f"[bold]Error message:[/bold] {error_message or 'No additional message provided.'}"
            f"\n\n[bold]What it means:[/bold] {guide.explanation}",
            title=title,
            border_style="cyan",
        )
    )

    causes = Table(title="Likely causes")
    causes.add_column("#", style="cyan", width=3)
    causes.add_column("What to check")
    for index, cause in enumerate(guide.causes, start=1):
        causes.add_row(str(index), cause)
    console.print(causes)

    fixes = Table(title="Recommended next steps")
    fixes.add_column("#", style="green", width=3)
    fixes.add_column("Action")
    for index, fix in enumerate(guide.fixes, start=1):
        fixes.add_row(str(index), fix)
    console.print(fixes)

    console.print(Panel(guide.example, title="Example", border_style="green"))
    console.print(
        "[dim]Rule-based guidance: verify the suggested cause against your code. "
        "DevAid does not execute or modify your project.[/dim]"
    )
