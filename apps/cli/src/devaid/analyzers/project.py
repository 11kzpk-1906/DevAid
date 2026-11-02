"""Basic project structure analyzer."""

from pathlib import Path

from rich.console import Console
from rich.table import Table

console = Console()


def _read_manifest_text(path: Path) -> str:
    """Read supported dependency manifests without executing project code."""
    manifest_names = (
        "pyproject.toml",
        "requirements.txt",
        "package.json",
        "pom.xml",
        "build.gradle",
        "Cargo.toml",
        "go.mod",
        "composer.json",
        "Gemfile",
        "pubspec.yaml",
        "Package.swift",
        "mix.exs",
    )
    contents: list[str] = []
    for name in manifest_names:
        manifest = path / name
        if manifest.is_file():
            try:
                contents.append(manifest.read_text(encoding="utf-8").lower())
            except (OSError, UnicodeError):
                continue
    return "\n".join(contents)


def _detect_frameworks(manifest_text: str) -> list[str]:
    """Identify common frameworks from dependency manifest text."""
    framework_markers = {
        "FastAPI": ("fastapi",),
        "Django": ("django",),
        "Flask": ("flask",),
        "React": ('"react"', "'react'"),
        "Next.js": ('"next"', "'next'"),
        "Vue": ('"vue"', "'vue'"),
        "Angular": ('"@angular/core"', "'@angular/core'"),
        "Svelte": ('"svelte"', "'svelte'"),
        "Express": ('"express"', "'express'"),
        "Spring Boot": ("spring-boot",),
        "Laravel": ("laravel/framework",),
        "Symfony": ("symfony/",),
        "Ruby on Rails": ("rails",),
        "Flutter": ("flutter",),
        "Gin": ("github.com/gin-gonic/gin",),
        "Fiber": ("github.com/gofiber/fiber",),
        "Axum": ("axum",),
        "Actix Web": ("actix-web",),
        "ASP.NET Core": ("microsoft.aspnetcore",),
        "Ktor": ("io.ktor",),
    }
    return [
        framework
        for framework, markers in framework_markers.items()
        if any(marker in manifest_text for marker in markers)
    ]


def _detect_package_managers(path: Path) -> list[str]:
    """Identify package managers from their lockfiles."""
    lockfiles = {
        "uv": ("uv.lock",),
        "Poetry": ("poetry.lock",),
        "Pipenv": ("Pipfile.lock",),
        "npm": ("package-lock.json", "npm-shrinkwrap.json"),
        "pnpm": ("pnpm-lock.yaml",),
        "Yarn": ("yarn.lock",),
        "Bun": ("bun.lock", "bun.lockb"),
        "Cargo": ("Cargo.lock",),
        "Go modules": ("go.sum",),
        "Composer": ("composer.lock",),
        "Bundler": ("Gemfile.lock",),
        "Pub": ("pubspec.lock",),
        "Swift Package Manager": ("Package.resolved",),
        "Mix": ("mix.lock",),
        "Gradle": ("gradle.lockfile",),
        "NuGet": ("packages.lock.json",),
    }
    return [
        manager
        for manager, files in lockfiles.items()
        if any((path / filename).is_file() for filename in files)
    ]


def analyze_project(path: Path) -> None:
    """Analyze a project's languages, frameworks, and structure."""
    if not path.exists() or not path.is_dir():
        console.print("[bold red]Error:[/bold red] Invalid project directory.")
        raise SystemExit(1)

    markers = {
        "Python": ["pyproject.toml", "requirements.txt", "setup.py"],
        "Node.js": ["package.json"],
        "Rust": ["Cargo.toml"],
        "Go": ["go.mod"],
        "Java": ["pom.xml", "build.gradle", "build.gradle.kts"],
        "Kotlin": ["build.gradle.kts", "settings.gradle.kts"],
        "PHP": ["composer.json"],
        "Ruby": ["Gemfile"],
        "Dart": ["pubspec.yaml"],
        "Swift": ["Package.swift"],
        "Elixir": ["mix.exs"],
        "C# / .NET": ["*.csproj", "*.sln"],
        "C / C++": ["CMakeLists.txt", "Makefile"],
    }

    detected = [
        language
        for language, files in markers.items()
        if any((path / file).exists() for file in files)
        or any(any(path.glob(file)) for file in files if "*" in file)
    ]
    manifest_text = _read_manifest_text(path)
    frameworks = _detect_frameworks(manifest_text)
    package_managers = _detect_package_managers(path)

    table = Table(title=f"DevAid Project Analysis — {path.resolve().name}")
    table.add_column("Check", style="cyan")
    table.add_column("Result", style="green")

    table.add_row("Project type", ", ".join(detected) if detected else "Unknown")
    table.add_row("Frameworks", ", ".join(frameworks) if frameworks else "Not detected")
    table.add_row(
        "Package managers",
        ", ".join(package_managers) if package_managers else "Not detected",
    )
    table.add_row("README", "Found" if (path / "README.md").exists() else "Missing")
    table.add_row("Git repository", "Found" if (path / ".git").exists() else "Not found")

    console.print(table)
