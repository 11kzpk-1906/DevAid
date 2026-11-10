"""Project-level configuration for DevAid diagnostics."""

import tomllib
from pathlib import Path

CONFIG_NAME = ".devaid.toml"
VALID_DOCTOR_CHECKS = {
    "health",
    "dependencies",
    "configuration",
    "deployment",
    "documentation",
    "security",
    "tests",
    "git",
    "release",
    "performance",
    "accessibility",
    "workflows",
    "docker",
    "packages",
    "python",
    "javascript",
    "environment",
}

DEFAULT_CONFIG = """# DevAid project configuration.
# Add diagnostic keys to skip selected checks in the full doctor run.
[doctor]
skip = []
"""


def load_skipped_checks(project_path: Path) -> set[str]:
    """Load and validate the optional project diagnostic profile."""
    config_path = project_path / CONFIG_NAME
    if not config_path.is_file():
        return set()

    try:
        with config_path.open("rb") as config_file:
            data = tomllib.load(config_file)
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise ValueError(f"Could not read {CONFIG_NAME}: {error}") from error

    doctor = data.get("doctor", {})
    if not isinstance(doctor, dict):
        raise ValueError("The [doctor] section must be a TOML table.")

    skipped = doctor.get("skip", [])
    if not isinstance(skipped, list) or not all(
        isinstance(item, str) for item in skipped
    ):
        raise ValueError("[doctor].skip must be an array of diagnostic names.")

    unknown = sorted(set(skipped) - VALID_DOCTOR_CHECKS)
    if unknown:
        raise ValueError("Unknown diagnostic names in [doctor].skip: " + ", ".join(unknown))

    return set(skipped)


def create_default_config(project_path: Path) -> Path:
    """Create a starter configuration without overwriting an existing file."""
    if not project_path.exists() or not project_path.is_dir():
        raise NotADirectoryError(f"Invalid project directory: {project_path}")
    config_path = project_path / CONFIG_NAME
    if config_path.exists():
        raise FileExistsError(f"{config_path} already exists; refusing to overwrite it.")
    config_path.write_text(DEFAULT_CONFIG, encoding="utf-8", newline="\n")
    return config_path
