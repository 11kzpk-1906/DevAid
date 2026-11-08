"""Check the latest published DevAid release without modifying the installation."""

from __future__ import annotations

import json
import re
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from rich.console import Console

from devaid import __version__

DEFAULT_REPOSITORY = "11kzpk-1906/DevAid"
VERSION_PATTERN = re.compile(
    r"^v?(\d+)\.(\d+)\.(\d+)(?:[-.]?(dev|a|b|rc)[.-]?(\d+))?$",
)
console = Console()


def version_key(version: str) -> tuple[int, int, int, int, int]:
    """Convert a simple semantic/PEP 440 version into a sortable key."""
    match = VERSION_PATTERN.fullmatch(version.strip())
    if match is None:
        raise ValueError(f"Unsupported version format: {version}")

    major, minor, patch = (int(match.group(index)) for index in (1, 2, 3))
    stage = match.group(4)
    stage_number = int(match.group(5) or 0)
    stage_rank = {None: 4, "rc": 3, "b": 2, "a": 1, "dev": 0}[stage]
    return major, minor, patch, stage_rank, stage_number


def fetch_latest_release(repository: str, timeout: float = 5.0) -> tuple[str, str] | None:
    """Return the latest release tag and URL, or None when no release exists."""
    url = f"https://api.github.com/repos/{repository}/releases/latest"
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "DevAid-Update-Checker",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )

    try:
        with urlopen(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        if error.code == 404:
            return None
        raise

    if not isinstance(payload, dict):
        raise ValueError("GitHub returned an unexpected release response.")

    tag = payload.get("tag_name")
    release_url = payload.get("html_url")
    if not isinstance(tag, str) or not isinstance(release_url, str):
        raise ValueError("GitHub's release response is missing its tag or URL.")

    return tag, release_url


def update_check(repository: str = DEFAULT_REPOSITORY) -> None:
    """Display whether a newer stable DevAid release is available."""
    current_version = __version__
    console.print(f"[bold cyan]DevAid update check[/bold cyan] — current: v{current_version}")

    try:
        latest = fetch_latest_release(repository)
        if latest is None:
            console.print("[yellow]No published stable release was found.[/yellow]")
            return

        latest_version, release_url = latest
        if version_key(latest_version) > version_key(current_version):
            console.print(f"[green]A newer release is available: {latest_version}[/green]")
            console.print(f"Release notes: {release_url}")
            console.print("This command only checks for updates; it does not install anything.")
        else:
            console.print("[green]You're up to date with the latest stable release.[/green]")
            console.print(f"Latest stable release: {latest_version}")
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError) as error:
        console.print(f"[yellow]Could not check for updates: {error}[/yellow]")
        console.print("Check your internet connection and try again.")
