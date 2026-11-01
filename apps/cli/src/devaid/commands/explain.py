"""Error explanation command."""

import typer
from rich.console import Console
from rich.panel import Panel

console = Console()


def explain(
    error: str = typer.Argument(..., help="The error message to explain."),
) -> None:
    """Explain common Python errors in beginner-friendly language."""

    error_types = {
        "ModuleNotFoundError": (
            "Python cannot find the module you're trying to import.",
            "Check whether the package is installed in your active environment.",
            "Try: uv add package-name",
        ),
        "ImportError": (
            "Python found a module but couldn't import the requested object.",
            "Check the spelling and availability of the imported name.",
            "Inspect the module and verify the import statement.",
        ),
        "SyntaxError": (
            "Python couldn't understand the code's syntax.",
            "Check missing colons, brackets, quotes, and indentation.",
            "Review the line number shown in the traceback.",
        ),
        "NameError": (
            "Your code references a variable or function Python doesn't know.",
            "Check spelling and whether the name was defined before use.",
            "Verify variable scope and initialization.",
        ),
        "TypeError": (
            "An operation received a value of an incompatible type.",
            "Check the types of the values used in the operation.",
            "Convert values where appropriate.",
        ),
    }

    matched = next(
        (name for name in error_types if name in error),
        None,
    )

    if matched is None:
        console.print(
            Panel(
                "DevAid couldn't identify this error yet.\n"
                "Try providing the complete Python error message.",
                title="Unknown Error",
                border_style="yellow",
            )
        )
        return

    description, cause, solution = error_types[matched]

    console.print(
        Panel(
            f"[bold]Error:[/bold] {matched}\n\n"
            f"[bold]Explanation:[/bold] {description}\n\n"
            f"[bold]Possible cause:[/bold] {cause}\n\n"
            f"[bold green]Suggested fix:[/bold green] {solution}",
            title="DevAid Error Explainer",
            border_style="cyan",
        )
    )