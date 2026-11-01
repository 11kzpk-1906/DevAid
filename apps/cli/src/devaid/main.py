"""DevAid CLI entry point."""

import typer
from rich.console import Console

app = typer.Typer(
    name="devaid",
    help="An open-source toolkit for developers.",
    no_args_is_help=True,
)

console = Console()


@app.callback()
def main() -> None:
    """Build better. Debug smarter. Ship confidently."""


@app.command()
def version() -> None:
    """Display the DevAid version."""
    from deveid import __version__

    console.print(f"[bold cyan]DevAid[/bold cyan] v{__version__}")


if __name__ == "__main__":
    app()
