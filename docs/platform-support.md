# Platform support

This page separates **published standalone binaries** from **source-installation compatibility** and records the evidence currently available for each.

## Published standalone binaries

The v0.2.0 GitHub Release contains these uploaded assets:

| Operating system | Architecture | Asset | Availability |
| --- | --- | --- | --- |
| Windows | x64 | `devaid-windows-x64.zip` | Published in v0.2.0 |
| Linux | x64 | `devaid-linux-x64.zip` | Published in v0.2.0 |
| macOS | ARM64 (Apple Silicon) | `devaid-macos-arm64.zip` | Published in v0.2.0 |

The release workflow defines matching build targets for these three platforms and smoke-tests each generated executable with `--help` and `version` before packaging it. New automated releases also publish a `SHA256SUMS.txt` manifest covering all three ZIP assets; the workflow verifies the manifest before attaching it to the release.

**Not published as standalone binaries:** Windows ARM64, Linux ARM64, macOS Intel (x86_64), and other architectures. This means no downloadable binary is currently offered for those targets; it does not establish that the Python source cannot run there.

## Running from source

The project metadata requires **Python 3.11 or newer**. Source installation uses `uv`:

```bash
git clone https://github.com/11kzpk-1906/DevAid.git
cd DevAid
uv sync --extra dev
uv run devaid --help
```

The evidence currently available is:

| Environment | Evidence | Status |
| --- | --- | --- |
| Ubuntu Linux, Python 3.11 | The CLI Tests GitHub Actions workflow installs Python 3.11 and runs pytest and Ruff | Automated CI |
| Windows, Python 3.14.7 | The v0.2.0 release notes record a local maintainer test | Locally tested; not CI |
| macOS, Python 3.11+ | No source-install test result is currently recorded | Not yet verified |
| Other OS / Python combinations | No test result is currently recorded | Not yet verified |

Python 3.11+ is the declared interpreter requirement, not a claim that every operating system and Python version has been tested. The automated source-test matrix covers Windows, Ubuntu Linux, and macOS on Python 3.11; other Python versions and operating systems remain unverified by CI.

## Browser tools

The tools in `web/` are static HTML, CSS, and JavaScript files intended to run in a modern browser. They do not require the Python CLI or a platform-specific executable. Some tools may need an internet connection for external resources or public API requests; see the README's Browser tools section for details.

## Support guidance

- Choose a standalone ZIP only when your OS and CPU architecture match the table above.\n- For releases that include `SHA256SUMS.txt`, verify the downloaded ZIP before extracting it; see the README for platform-specific commands.
- For other environments, a Python source installation may work if Python 3.11+ and its dependencies are available, but those combinations are not currently verified by the project's CI.
- Do not assume that a Windows x64 binary runs on Windows ARM64, or that an Apple Silicon binary runs natively on an Intel Mac.
- Platform coverage may change in later releases. Check the assets attached to the current [GitHub Release](https://github.com/11kzpk-1906/DevAid/releases) before downloading.

## Evidence sources

- [v0.2.0 release and uploaded assets](https://github.com/11kzpk-1906/DevAid/releases/tag/v0.2.0)
- [Standalone binary build workflow](https://github.com/11kzpk-1906/DevAid/blob/main/.github/workflows/release-binaries.yml)
- [CLI Tests workflow](https://github.com/11kzpk-1906/DevAid/blob/main/.github/workflows/cli-tests.yml)
- [Project Python requirement](https://github.com/11kzpk-1906/DevAid/blob/main/pyproject.toml)
- [v0.2.0 release notes](https://github.com/11kzpk-1906/DevAid/releases/tag/v0.2.0)
