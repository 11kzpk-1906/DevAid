from pathlib import Path

from devaid.analyzers.project import _detect_languages, _detect_package_managers


def test_detect_languages_supports_additional_ecosystems(tmp_path: Path) -> None:
    for filename in ("composer.json", "Gemfile", "api.csproj", "CMakeLists.txt"):
        (tmp_path / filename).touch()

    detected = _detect_languages(tmp_path)

    assert "PHP" in detected
    assert "Ruby" in detected
    assert "C# / .NET" in detected
    assert "C / C++" in detected


def test_detect_languages_detects_kotlin_and_java_gradle_projects(
    tmp_path: Path,
) -> None:
    (tmp_path / "build.gradle.kts").touch()

    detected = _detect_languages(tmp_path)

    assert "Java" in detected
    assert "Kotlin" in detected


def test_detect_package_managers_includes_composer_and_bundler(
    tmp_path: Path,
) -> None:
    (tmp_path / "composer.lock").touch()
    (tmp_path / "Gemfile.lock").touch()

    detected = _detect_package_managers(tmp_path)

    assert "Composer" in detected
    assert "Bundler" in detected
