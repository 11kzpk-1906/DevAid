from pathlib import Path

import pytest
from devaid.settings import create_default_config, load_skipped_checks


def test_profile_loads_skip_list(tmp_path: Path) -> None:
    config = tmp_path / ".devaid.toml"
    config.write_text('[doctor]\nskip = ["security"]\n', encoding="utf-8")
    assert load_skipped_checks(tmp_path) == {"security"}


def test_profile_rejects_unknown_key(tmp_path: Path) -> None:
    config = tmp_path / ".devaid.toml"
    config.write_text('[doctor]\nskip = ["unknown"]\n', encoding="utf-8")
    with pytest.raises(ValueError):
        load_skipped_checks(tmp_path)


def test_config_creation_refuses_overwrite(tmp_path: Path) -> None:
    config = create_default_config(tmp_path)
    with pytest.raises(FileExistsError):
        create_default_config(tmp_path)
    assert config.exists()
