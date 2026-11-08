# DevAid

<p align="center">
  <strong>Build better. Debug smarter. Ship confidently.</strong>
  <br />
  A free, open-source, local-first toolkit for everyday developer workflows.
</p>

<p align="center">
  <a href="https://github.com/11kzpk-1906/DevAid/releases/latest"><img alt="Latest release" src="https://img.shields.io/github/v/release/11kzpk-1906/DevAid?display_name=tag" /></a>
  <a href="https://github.com/11kzpk-1906/DevAid/blob/main/LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/License-MIT-blue.svg" /></a>
  <img alt="Free core tools" src="https://img.shields.io/badge/Core%20Tools-Free-2ea44f" />
  <a href="https://github.com/11kzpk-1906/DevAid/actions"><img alt="CI" src="https://github.com/11kzpk-1906/DevAid/actions/workflows/cli-tests.yml/badge.svg" /></a>
</p>

---

## What is DevAid?

**DevAid helps developers understand, inspect, and improve their projects without depending on a paid cloud service or an AI API.**

It brings together a Python command-line interface (CLI) and a collection of static browser tools. The CLI focuses on local project diagnostics, while the browser tools help with common development tasks such as inspecting JSON, comparing text, checking configuration, and understanding Git commands.

DevAid is designed to be useful without AI. Local-first behavior is preferred, and network access is limited to features that explicitly need it.

## Highlights

- **Local-first diagnostics:** inspect project structure, configuration, dependencies, tests, security hygiene, and more.
- **Cross-platform releases:** downloadable CLI bundles for Windows x64, Linux x64, and macOS ARM64.
- **Browser utilities:** use practical tools directly in your browser.
- **No paid API required:** core functionality does not depend on a subscription or paid AI service.
- **Open source:** inspect the code, report issues, and contribute improvements.

## Download DevAid

The latest stable release is **v0.1.0**.

**[Download DevAid v0.1.0](https://github.com/11kzpk-1906/DevAid/releases/tag/v0.1.0)**

| Platform | Release asset | Architecture |
| --- | --- | --- |
| Windows | `devaid-windows-x64.zip` | x64 |
| Linux | `devaid-linux-x64.zip` | x64 |
| macOS | `devaid-macos-arm64.zip` | Apple Silicon (ARM64) |

### Run the standalone CLI

1. Download the ZIP for your operating system from the release page.
2. Extract the ZIP to a folder.
3. Open a terminal in the extracted folder.
4. Run the executable:

**Windows (PowerShell):**
```powershell
.\devaid.exe --help
.\devaid.exe version
.\devaid.exe doctor .
```

**Linux:**
```bash
chmod +x ./devaid
./devaid --help
./devaid version
./devaid doctor .
```

**macOS (Apple Silicon):**
```bash
chmod +x ./devaid
./devaid --help
./devaid version
./devaid doctor .
```

If your shell cannot find the executable, run it from the extracted directory using the relative path shown above. You can optionally add that directory to your PATH.

> **Platform note:** the published bundles target Windows x64, Linux x64, and macOS ARM64. The macOS bundle is for Apple Silicon; Intel Mac support is not currently listed as a release target.

## Available CLI commands

Run `devaid --help` to see the commands available in your installed version. Commands that accept a project path generally use the current directory when you pass `.`.

| Command | Purpose |
| --- | --- |
| `devaid version` | Display the installed version. |
| `devaid welcome` (or `devaid welcome --path PATH`) | Open a guided first-run menu for common tasks. |\n| `devaid update-check` | Check GitHub for the latest stable release without installing it. |
| `devaid explain` | Explain supported programming errors and suggest troubleshooting steps. |
| `devaid analyze PATH` | Identify project languages, frameworks, and package managers. |
| `devaid deps PATH` | Inspect dependency manifests offline. |
| `devaid doctor PATH` | Run the full set of local project diagnostics. |
| `devaid suggest PATH` | Recommend practical project setup improvements. |
| `devaid test-doctor PATH` | Check test and CI readiness without running the test suite. |
| `devaid git PATH` | Review Git repository state without changing it. |
| `devaid release PATH` | Check release metadata and readiness. |
| `devaid performance PATH` | Run static performance-hygiene checks. |
| `devaid accessibility PATH` | Inspect HTML for common accessibility issues. |
| `devaid deploy PATH` | Review common deployment configuration files offline. |
| `devaid health PATH` | Generate a project health report. |
| `devaid config PATH` | Check common configuration and ignore-file hygiene. |
| `devaid env` | Report local development environment information. |
| `devaid api URL` | Send a read-only HTTP GET and inspect the response. |
| `devaid docs PATH` | Check documentation file and section completeness. |
| `devaid security PATH` | Scan local project files for common secret and security hygiene issues. |
| `devaid workflow-doctor PATH` | Review GitHub Actions permissions, action pinning, and checkout credential settings. |
| `devaid docker-doctor PATH` | Review Dockerfiles and Compose files for common security and reliability issues. |
| `devaid package-doctor PATH` | Check Python and Node.js manifests and lockfile consistency. |
| `devaid python-doctor PATH` | Review Python project structure and requirements hygiene. |
| `devaid javascript-doctor PATH` | Review Node.js metadata and project hygiene. |
| `devaid report PATH` | Export supported findings as Markdown or JSON. |
| `devaid plugins` | List installed analyzer plugins without importing plugin code. |
| `devaid plugin-run NAME PATH` | Explicitly load and run one installed analyzer plugin. |
| `devaid dashboard PATH` | Open an interactive terminal menu for common diagnostics. |
| `devaid config-init PATH` | Create a starter `.devaid.toml` diagnostic profile. |

Use `devaid COMMAND --help` for command-specific options.

## Install and run from source

For contributors or users who prefer running DevAid from Python:

**Requirements:** Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/11kzpk-1906/DevAid.git
cd DevAid
uv sync --extra dev
uv run devaid --help
uv run devaid doctor .
```

Run the development checks:

```bash
uv run ruff check .
uv run pytest
```

## Browser tools

The static browser-tools MVP in `web/` includes:

- JSON Inspector and Regex Tester
- URL Encoder / Decoder and line-based Text Diff
- YAML Validator
- Docker Compose Checker and Dockerfile Analyzer
- GitHub Actions Workflow Checker
- GitHub Repository Health Checker, Topics Analyzer, and Repository Scorecard
- README Analyzer and Markdown Previewer
- Git Command Explainer and `.gitignore` Generator
- Changelog Generator and Commit Message Assistant
- License Notes Guide
- Dependency Manifest Checker
- Environment Template Doctor
- API Response Inspector

Most tools process input in the browser tab. No backend is required, and project source files are not uploaded by these tools. The Repository Health Checker makes read-only requests to GitHub's public API. YAML parsing uses the open-source js-yaml parser loaded from jsDelivr, so an internet connection is needed for that tool.

**Limitations:** the Dependency Manifest Checker is not a vulnerability scanner; the License Notes Guide is not legal advice; the API Response Inspector does not send requests; and Dockerfile / Compose checks are heuristic rather than authoritative validators. The browser MVP does not execute the Python CLI or inspect local project folders.

To use the browser tools, open the files in the repository's `web/` directory. The tools and documentation can be hosted as static files.

## Technology

- **CLI:** Python and Typer
- **Terminal output:** Rich
- **Packaging:** Hatchling
- **Development tooling:** uv, Ruff, and pytest
- **Browser utilities:** HTML, CSS, and JavaScript

The CLI recognizes project markers for Python, Node.js, Rust, Go, Java, Kotlin, PHP, Ruby, Dart, Swift, Elixir, C#/.NET, and C/C++. Package-manager detection covers common ecosystems and their manifest or lock files. Detection is based on project files and manifest text; mixed-language projects may be identified as using multiple languages.

## Custom diagnostic configuration

Run `devaid config-init .` to create a `.devaid.toml` starter profile without overwriting an existing file.

Example:

```toml
[doctor]
skip = ["accessibility", "performance"]
```

The full doctor validates the configuration before running. Supported skip keys include health, dependencies, configuration, deployment, documentation, security, tests, Git, release, performance, accessibility, workflows, Docker, packages, Python, JavaScript, and environment. Skipping a report does not change the underlying diagnostic rules.

## Analyzer plugins

DevAid supports optional Python analyzer plugins through the `devaid.analyzers` entry-point group.

Example package metadata:

```toml
[project.entry-points."devaid.analyzers"]
my-check = "my_package.devaid_plugin:analyze"
```

The plugin callback accepts a project path. Use `devaid plugins` to list installed plugin names and `devaid plugin-run my-check .` to run one explicitly. Listing plugins reads entry-point metadata only; a plugin module is imported only when selected.

> Third-party plugins are executable Python code. Install plugins only from sources you trust.

## Zero-cost principles

DevAid aims to keep core development and usage free:

- No required paid AI API.
- No required paid hosting or database.
- No subscription for core local tools.
- Prefer free and open-source dependencies.
- Avoid infrastructure when a local implementation is sufficient.

Third-party services may have their own limits or change their free offerings. Essential local functionality should not depend on a paid service.

## Privacy and security

Developer projects may contain credentials, private source code, customer data, and other sensitive information. DevAid is designed to favor local analysis and make network activity understandable.

- Avoid printing or transmitting secrets unnecessarily.
- Redact sensitive values from diagnostic output where feasible.
- Make network access explicit.
- Ask for informed consent before sending project data to an external service.
- Treat findings as guidance to verify, not as a guarantee that a project is secure.

Please do not include real credentials, access tokens, private keys, or confidential project data in issues or discussions.

## Roadmap

DevAid is being developed incrementally. Completed work includes:

- [x] Python CLI foundation and command interface.
- [x] Local project analysis and supported error explanations.
- [x] Dependency, configuration, environment, documentation, and project-health diagnostics.
- [x] Deployment, security, Git, release, test-readiness, and performance diagnostics.
- [x] HTML accessibility hygiene checks.
- [x] GitHub Actions workflow and Docker / Compose hygiene checks.
- [x] Python, JavaScript, package-manager, and multi-language project detection.
- [x] Markdown and JSON diagnostic report export.
- [x] Interactive CLI dashboard, custom diagnostic profiles, and analyzer plugin extension points.
- [x] Static browser utilities for common developer workflows.
- [x] Cross-platform binary build workflow and v0.1.0 release.

Potential next areas include smoother onboarding, update notifications, broader platform testing, and richer diagnostic explanations. Roadmap items are not promises or claims of completed functionality.

## Contributing

Contributions are welcome, including bug reports, documentation improvements, tests, and new tools.

Before opening a pull request:

1. Check existing issues for related reports.
2. Explain the problem your change solves.
3. Add tests for new behavior where practical.
4. Update documentation when commands or behavior change.
5. Keep changes focused and avoid unnecessary dependencies.

Please be respectful and constructive when interacting with other contributors. See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidance.

## Community and support

- **Bug reports and feature ideas:** [GitHub Issues](https://github.com/11kzpk-1906/DevAid/issues)
- **Code contributions:** [Open a Pull Request](https://github.com/11kzpk-1906/DevAid/pulls)
- **Releases and downloads:** [GitHub Releases](https://github.com/11kzpk-1906/DevAid/releases)

## License

DevAid is licensed under the [MIT License](LICENSE).

---

<p align="center">
  Made for developers, by the open-source community.
  <br />
  <strong>Build better. Debug smarter. Ship confidently.</strong>
</p>
