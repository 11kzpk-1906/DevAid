import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()
_TIMEOUT_SECONDS = 8
_MAX_RESPONSE_BYTES = 1_000_000


def inspect_api(url: str) -> None:
    """Send a read-only GET request and summarize the endpoint response."""
    parsed = urlsplit(url)

    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        console.print(
            "[bold red]Invalid URL:[/bold red] Provide a complete http:// or https:// URL."
        )
        raise typer.Exit(code=2)

    if parsed.username or parsed.password:
        console.print(
            "[bold red]Invalid URL:[/bold red] Do not place credentials in the URL."
        )
        raise typer.Exit(code=2)

    request = Request(
        url,
        headers={"User-Agent": "DevAid-API-Doctor/0.1", "Accept": "*/*"},
        method="GET",
    )
    started = time.perf_counter()

    try:
        try:
            response = urlopen(request, timeout=_TIMEOUT_SECONDS)
        except HTTPError as error:
            response = error

        with response:
            status_code = response.status
            headers = response.headers
            content_type = headers.get("Content-Type", "Not provided")
            body = response.read(_MAX_RESPONSE_BYTES + 1)
    except (URLError, TimeoutError, OSError, ValueError) as error:
        console.print(
            Panel(
                f"Could not reach the endpoint.\n\n[bold]Reason:[/bold] {error}",
                title="API Doctor",
                border_style="red",
            )
        )
        raise typer.Exit(code=1) from error

    elapsed_ms = (time.perf_counter() - started) * 1000
    is_json = "json" in content_type.lower()
    json_result = "Not checked (response is not labelled JSON)"

    if is_json:
        if len(body) > _MAX_RESPONSE_BYTES:
            json_result = "Skipped (response exceeds 1 MB inspection limit)"
        else:
            try:
                json.loads(body)
                json_result = "Valid JSON"
            except (UnicodeDecodeError, json.JSONDecodeError):
                json_result = "Invalid JSON"

    table = Table(title="DevAid API Doctor")
    table.add_column("Check", style="cyan")
    table.add_column("Result")

    status_style = "green" if 200 <= status_code < 300 else "yellow"
    table.add_row("HTTP status", f"[{status_style}]{status_code}[/{status_style}]")
    table.add_row("Response time", f"{elapsed_ms:.1f} ms")
    table.add_row("Content-Type", content_type)
    table.add_row("JSON validation", json_result)

    if parsed.scheme == "https":
        for header in (
            "Strict-Transport-Security",
            "X-Content-Type-Options",
            "Content-Security-Policy",
        ):
            table.add_row(
                header,
                "Present" if headers.get(header) else "Not present",
            )

    console.print(table)
    if status_code >= 400:
        console.print("[yellow]The endpoint returned an HTTP error status.[/yellow]")
    console.print(
        "[dim]Read-only GET request. DevAid does not submit data, follow API "
        "workflows, or display response bodies. Inspection is limited to 1 MB.[/dim]"
    )
