"""DevAid CLI entry point."""

import typer
from rich.console import Console

from devaid import __version__
from devaid.analyzers.project import analyze_project
from devaid.commands.explain import explain
from devaid.diagnostics.api import inspect_api
from devaid.diagnostics.config import check_config
from devaid.diagnostics.dependencies import check_dependencies
from devaid.diagnostics.deployment import check_deployment
from devaid.diagnostics.doctor import run_doctor
from devaid.diagnostics.documentation import check_documentation
from devaid.diagnostics.environment import check_environment
from devaid.diagnostics.git import git_doctor
from devaid.diagnostics.health import health_check
from devaid.diagnostics.security import check_security
from devaid.diagnostics.suggestions import show_suggestions
from devaid.diagnostics.test_doctor import test_doctor

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
app.command(name="deps")(check_dependencies)
app.command(name="doctor")(run_doctor)
app.command(name="suggest")(show_suggestions)
app.command(name="test-doctor")(test_doctor)
app.command(name="git")(git_doctor)
app.command(name="deploy")(check_deployment)
app.command(name="health")(health_check)
app.command(name="config")(check_config)
app.command(name="env")(check_environment)
app.command(name="api")(inspect_api)
app.command(name="docs")(check_documentation)
app.command(name="security")(check_security)

if __name__ == "__main__":
    app()
