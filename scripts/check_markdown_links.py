"""Check local Markdown links without making network requests.

Usage:
    python scripts/check_markdown_links.py
    python scripts/check_markdown_links.py README.md docs/
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import unquote, urlsplit

LINK_RE = re.compile(r"!?(?:\[[^\]]*\])\((?:<([^>]+)>|([^\s)]+))(?:\s+[^)]*)?\)")
REFERENCE_RE = re.compile(r"^\s*\[([^\]]+)\]:\s*(?:<([^>]+)>|(\S+))", re.MULTILINE)
HEADING_RE = re.compile(r"^#{1,6}\s+(.+?)\s*#*\s*$", re.MULTILINE)
HTML_ID_RE = re.compile(r"""\bid\s*=\s*["']([^"']+)["']""", re.IGNORECASE)
FENCE_RE = re.compile(r"^\s*(`{3,}|~{3,}).*$", re.MULTILINE)


def _without_code_blocks(text: str) -> str:
    lines = text.splitlines()
    output: list[str] = []
    fence_char: str | None = None
    fence_size = 0
    for line in lines:
        match = re.match(r"^\s*(`{3,}|~{3,})", line)
        if match:
            marker = match.group(1)
            if fence_char is None:
                fence_char, fence_size = marker[0], len(marker)
            elif marker[0] == fence_char and len(marker) >= fence_size:
                fence_char, fence_size = None, 0
            output.append("")
        elif fence_char is None:
            output.append(line)
        else:
            output.append("")
    return "\n".join(output)


def _slug_heading(heading: str) -> str:
    heading = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", heading)
    heading = heading.strip().lower()
    heading = re.sub(r"[^\w\- ]", "", heading)
    return re.sub(r"\s+", "-", heading.strip())


def _anchors(text: str) -> set[str]:
    clean = _without_code_blocks(text)
    anchors = set(HTML_ID_RE.findall(clean))
    counts: dict[str, int] = {}
    for heading in HEADING_RE.findall(clean):
        slug = _slug_heading(heading)
        count = counts.get(slug, 0)
        anchors.add(slug if count == 0 else f"{slug}-{count}")
        counts[slug] = count + 1
    return anchors


def _markdown_files(paths: list[Path]) -> list[Path]:
    found: set[Path] = set()
    for path in paths:
        if path.is_file() and path.suffix.lower() in {".md", ".markdown"}:
            found.add(path.resolve())
        elif path.is_dir():
            found.update(
                item.resolve()
                for item in path.rglob("*")
                if item.is_file() and item.suffix.lower() in {".md", ".markdown"}
            )
    return sorted(found)


def check_file(path: Path) -> list[str]:
    try:
        original = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as exc:
        return [f"{path}: cannot read Markdown file: {exc}"]

    text = _without_code_blocks(original)
    errors: list[str] = []
    references = {
        label.casefold(): (angle or plain)
        for label, angle, plain in REFERENCE_RE.findall(text)
    }

    # Inline links and images.
    targets = [angle or plain for angle, plain in LINK_RE.findall(text)]

    # Reference-style links: [label] or [label][reference].
    for match in re.finditer(r"!?\[([^\]]+)\](?:\[([^\]]*)\])?", text):
        label, reference = match.groups()
        if match.start() > 0 and text[match.start() - 1] == "!":
            continue
        key = (reference or label).casefold()
        if key in references:
            targets.append(references[key])

    for target in targets:
        target = target.strip()
        if not target or target.startswith("#"):
            fragment = unquote(target[1:])
            if fragment and fragment not in _anchors(original):
                errors.append(f"{path}: missing anchor #{fragment}")
            continue

        parsed = urlsplit(target)
        if parsed.scheme or parsed.netloc:
            continue
        if target.startswith("//"):
            continue

        raw_path = unquote(parsed.path)
        if not raw_path:
            if parsed.fragment and unquote(parsed.fragment) not in _anchors(original):
                errors.append(f"{path}: missing anchor #{unquote(parsed.fragment)}")
            continue

        destination = (path.parent / raw_path).resolve()
        if not destination.exists():
            errors.append(f"{path}: broken local link '{target}'")
            continue
        if (
            parsed.fragment
            and destination.is_file()
            and destination.suffix.lower() in {".md", ".markdown"}
        ):
            try:
                destination_text = destination.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            fragment = unquote(parsed.fragment)
            if fragment not in _anchors(destination_text):
                errors.append(f"{path}: missing anchor '{fragment}' in '{raw_path}'")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "paths",
        nargs="*",
        type=Path,
        help="Markdown files or directories (default: repository root)",
    )
    args = parser.parse_args()
    roots = args.paths or [Path(__file__).resolve().parents[1]]
    files = _markdown_files(roots)
    if not files:
        print("No Markdown files found.")
        return 0

    errors = [error for path in files for error in check_file(path)]
    if errors:
        print("\n".join(errors), file=sys.stderr)
        print(f"Found {len(errors)} broken local Markdown link(s) across {len(files)} file(s).")
        return 1

    print(f"Checked {len(files)} Markdown file(s): all local links are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
