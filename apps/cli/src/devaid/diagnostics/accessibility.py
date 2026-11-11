import os
from html.parser import HTMLParser
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

console = Console()

SKIP_DIRS = {
    ".git", ".venv", "venv", "node_modules", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", "dist", "build", ".next", ".nuxt",
    "coverage", "target",
}
MAX_FILES = 3000
MAX_FILE_BYTES = 2 * 1024 * 1024


class AccessibilityParser(HTMLParser):
    """Collect common accessibility issues from an HTML document."""

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.images_missing_alt = 0
        self.controls_without_label = 0
        self.links_without_name = 0
        self.buttons_without_name = 0
        self.has_language = False
        self.has_title = False
        self._label_ids: set[str] = set()
        self._pending_controls: list[dict[str, str | bool]] = []
        self._active_label = False
        self._active_link = False
        self._active_button = False
        self._link_has_name = False
        self._button_has_name = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = {key: value or "" for key, value in attrs}
        if tag == "html" and values.get("lang", "").strip():
            self.has_language = True
        elif tag == "title":
            self.has_title = True
        elif tag == "img" and "alt" not in values:
            self.images_missing_alt += 1
        elif tag == "label":
            self._active_label = True
            if values.get("for"):
                self._label_ids.add(values["for"])
        elif tag in {"input", "select", "textarea"}:
            input_type = values.get("type", "").lower()
            if tag == "input" and input_type in {"hidden", "submit", "button", "reset"}:
                return
            self._pending_controls.append(
                {
                    "id": values.get("id", ""),
                    "labelled": bool(
                        values.get("aria-label") or values.get("aria-labelledby")
                    ),
                    "inside_label": self._active_label,
                }
            )
        elif tag == "a":
            self._active_link = True
            self._link_has_name = bool(
                values.get("aria-label") or values.get("aria-labelledby")
                or values.get("title") or values.get("img")
            )
        elif tag == "button":
            self._active_button = True
            self._button_has_name = bool(
                values.get("aria-label") or values.get("aria-labelledby")
                or values.get("title")
            )

    def handle_endtag(self, tag: str) -> None:
        if tag == "label":
            self._active_label = False
        elif tag == "a":
            if self._active_link and not self._link_has_name:
                self.links_without_name += 1
            self._active_link = False
        elif tag == "button":
            if self._active_button and not self._button_has_name:
                self.buttons_without_name += 1
            self._active_button = False

    def handle_data(self, data: str) -> None:
        if data.strip():
            if self._active_link:
                self._link_has_name = True
            if self._active_button:
                self._button_has_name = True

    def finalize(self) -> None:
        for control in self._pending_controls:
            has_id = str(control["id"]) in self._label_ids and bool(control["id"])
            if not (control["labelled"] or control["inside_label"] or has_id):
                self.controls_without_label += 1


def inspect_accessibility(path: Path) -> list[tuple[str, str, str]]:
    """Inspect HTML files without executing scripts or contacting a network."""
    findings: list[tuple[str, str, str]] = []
    html_files: list[Path] = []
    scanned = 0
    truncated = False

    for current, directories, files in os.walk(path):
        directories[:] = [name for name in directories if name not in SKIP_DIRS]
        for filename in files:
            scanned += 1
            if scanned > MAX_FILES:
                truncated = True
                break
            item = Path(current) / filename
            if item.suffix.lower() in {".html", ".htm"}:
                html_files.append(item)
        if truncated:
            break

    if not html_files:
        findings.append(
            (
                "HTML coverage",
                "INFO",
                "No HTML files found; JSX and template files are not parsed",
            )
        )
        findings.append(
            (
                "Accessibility scan",
                "INFO",
                "No HTML documents were available to inspect",
            )
        )
    else:
        totals = {
            "images": 0,
            "controls": 0,
            "links": 0,
            "buttons": 0,
            "language": 0,
            "title": 0,
        }
        parsed = 0
        unreadable = 0

        for html_file in html_files:
            try:
                if html_file.stat().st_size > MAX_FILE_BYTES:
                    unreadable += 1
                    continue
                source = html_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                unreadable += 1
                continue

            parser = AccessibilityParser()
            try:
                parser.feed(source)
                parser.close()
            except Exception:
                unreadable += 1
                continue
            parser.finalize()
            parsed += 1
            totals["images"] += parser.images_missing_alt
            totals["controls"] += parser.controls_without_label
            totals["links"] += parser.links_without_name
            totals["buttons"] += parser.buttons_without_name
            totals["language"] += int(not parser.has_language)
            totals["title"] += int(not parser.has_title)

        checks = (
            ("Images", "images", "image(s) are missing an alt attribute"),
            ("Form controls", "controls", "form control(s) may lack an accessible label"),
            ("Links", "links", "link(s) may have no accessible name"),
            ("Buttons", "buttons", "button(s) may have no accessible name"),
            ("Document language", "language", "document(s) are missing an html lang attribute"),
            ("Document title", "title", "document(s) are missing a title element"),
        )
        for label, key, description in checks:
            count = totals[key]
            findings.append(
                (
                    label,
                    "REVIEW" if count else "PASS",
                    f"{count} {description}" if count else "No issues detected by this check",
                )
            )
        findings.append(
            (
                "HTML coverage",
                "PASS" if parsed else "REVIEW",
                f"Inspected {parsed} HTML file(s)"
                + (f"; skipped {unreadable} unreadable or oversized file(s)" if unreadable else ""),
            )
        )

    findings.append(
        (
            "Scan coverage",
            "INFO" if truncated else "PASS",
            f"Inspected metadata for {min(scanned, MAX_FILES)} file(s)"
            + ("; scan stopped at the 3,000-file safety limit" if truncated else ""),
        )
    )
    return findings


def accessibility_doctor(path: Path) -> None:
    """Display static HTML accessibility hygiene findings."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise typer.Exit(code=1)

    findings = inspect_accessibility(path)
    table = Table(title=f"DevAid Accessibility Doctor — {path.resolve().name}")
    table.add_column("Area", style="cyan")
    table.add_column("Status")
    table.add_column("Details")
    styles = {"PASS": "green", "REVIEW": "yellow", "ERROR": "red", "INFO": "blue"}
    for area, status, details in findings:
        table.add_row(area, f"[{styles[status]}]{status}[/{styles[status]}]", details)
    console.print(table)

    passed = sum(status == "PASS" for _, status, _ in findings)
    review = sum(status == "REVIEW" for _, status, _ in findings)
    errors = sum(status == "ERROR" for _, status, _ in findings)
    info = sum(status == "INFO" for _, status, _ in findings)
    console.print(
        f"\\n[bold]Final summary:[/bold] {passed} passed • {review} to review • "
        f"{errors} errors • {info} informational"
    )
    console.print(
        "[dim]Static HTML checks only. This is not a complete WCAG audit; "
        "manual keyboard, screen-reader, contrast, and interaction testing is still needed.[/dim]"
    )
