"""DevAid CLI entry point."""

import typer
from rich.console import Console

from devaid import __version__
from devaid.analyzers.project import analyze_project
from devaid.commands.explain import explain

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
    console.print(f"[bold cyan]DevAid[/bold cyan] v{__version__}")


app.command(name="explain")(explain)
app.command(name="analyze")(analyze_project)



if __name__ == "__main__":
    app()