# DevAid

<p align="center">
  <strong>Build better. Debug smarter. Ship confidently.</strong>
  <br />
  An open-source, local-first toolkit that helps developers solve everyday development problems.
</p>

<p align="center">
  <img alt="License: MIT" src="https://img.shields.io/badge/License-MIT-blue.svg" />
  <img alt="Open source" src="https://img.shields.io/badge/Open%20Source-Community%20Driven-brightgreen" />
  <img alt="Cost" src="https://img.shields.io/badge/Core%20Tools-Free-2ea44f" />
  <img alt="Status" src="https://img.shields.io/badge/Status-Early%20Development-orange" />
</p>

---

## What is DevAid?

**DevAid is a free, open-source developer toolkit with a web platform and command-line interface (CLI).** Its goal is to make common development tasks easier to understand and troubleshoot—whether you're learning to code, maintaining a production application, or contributing to open source.

The project is being designed around practical diagnostics rather than requiring every task to go through an AI chatbot. Core tools should work locally wherever possible, with AI treated as an optional enhancement—not a requirement.

> **Project status:** The Python CLI is actively being built, with offline diagnostics and automated tests. The web platform is a static browser-tools MVP. See the implemented commands and tools below.

## Our goals

- **Free by design:** Keep the core experience usable without paid APIs or subscriptions.
- **Local-first:** Prefer running diagnostics on the developer's own machine.
- **Privacy-conscious:** Do not upload source code, logs, or project files without clear user consent.
- **Useful without AI:** Build deterministic tools first; make AI integrations optional.
- **Developer-friendly:** Support different experience levels, languages, and workflows.
- **Open to everyone:** Welcome contributions, feedback, bug reports, and ideas.

## Available CLI tools

The following commands are implemented in the Python CLI. Most diagnostics are read-only and run locally.

| Command | What it does |
| --- | --- |
| `devaid version` | Display the installed DevAid version. |
| `devaid explain` | Explain supported programming errors and suggest troubleshooting steps. |
| `devaid analyze PATH` | Identify project languages, frameworks, and package managers. |
| `devaid deps PATH` | Inspect dependency manifests offline. |
| `devaid doctor PATH` | Run the complete set of local project diagnostics and prioritized suggestions. |
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

Run `devaid --help` or `devaid COMMAND --help` for command-specific options. Commands that accept a project path generally use the current directory when you pass `.`.

### Install and run from source

Requirements: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/11kzpk-1906/DevAid.git
cd DevAid
uv sync --extra dev
uv run devaid --help
uv run devaid doctor .
```

For development checks:

```bash
uv run ruff check .
uv run pytest
```

### Web tools

The static browser-tools MVP in `web/` includes a JSON Inspector, Regex Tester, URL Encoder / Decoder, line-based Text Diff, and a YAML Validator. The tools process input in the browser tab; no project files are uploaded and no backend is required. Text Diff uses a bounded local comparison to keep memory use predictable. YAML parsing uses the open-source js-yaml parser loaded from jsDelivr; the YAML text itself is parsed in the browser and is not uploaded. An internet connection is required to load the parser.

- Open browser tools from the repository's `web/` directory.
- Read the static documentation in `docs/`.
- Both can be hosted as static files without a paid backend or database.
- The browser MVP does not execute the Python CLI or inspect local project folders.

## Technology direction

The current CLI implementation uses Python and Typer. The planned web platform is expected to use:

- **Web:** React, TypeScript, and Tailwind CSS
- **CLI:** Python and Typer (implemented)
- **Optional API:** Python and FastAPI, only where a hosted service is genuinely needed
- **Local data:** Files and lightweight local storage where practical
- **Testing:** Automated tests and CI checks

These are planned choices and may evolve as the architecture is validated.

## Zero-cost operating principles

DevAid aims to keep its development and core usage at **zero mandatory cost**:

- No required paid AI API.
- No required paid hosting or database.
- No subscription required for core local tools.
- Prefer free and open-source dependencies.
- Avoid infrastructure when a local implementation is sufficient.

Third-party services may have their own limits or change their free offerings. DevAid should not depend on a paid service to deliver its essential local functionality.

## Privacy and security

Developer projects can contain credentials, private source code, customer data, and other sensitive information. DevAid should handle that material carefully.

- Local analysis is the default design preference.
- Never print or transmit secrets unnecessarily.
- Redact sensitive values from diagnostic output where feasible.
- Make any network access explicit and understandable.
- Ask for informed consent before sending project data to an external service.
- Treat security findings as guidance that should be verified, not as a guarantee that a project is secure.

Please do not submit real credentials, access tokens, private keys, or confidential project data in issues or discussions.

## Roadmap

The project is being developed incrementally:

- [x] Establish repository structure, contribution guidelines, and automated checks.
- [x] Build the Python CLI foundation and command interface.
- [x] Implement local project analysis and error explanation.
- [x] Add offline dependency, configuration, environment, documentation, and project health checks.
- [x] Add deployment, security, Git, release, test-readiness, and performance diagnostics.
- [x] Add HTML accessibility hygiene checks.
- [x] Add GitHub Actions workflow hygiene checks.
- [x] Add Dockerfile and Docker Compose hygiene checks.
- [ ] Expand CLI language and framework coverage based on real-world feedback.
- [x] Add a static browser-tools MVP (JSON Inspector and Regex Tester).
- [x] Add a static documentation landing page.
- [x] Add package-manager, Python, and JavaScript diagnostics plus Markdown/JSON report export.
- [x] Add browser-native URL encoding and decoding.
- [x] Add a local line-based Text Diff tool.\n- [x] Add YAML validation and formatting in the browser.
- [ ] Expand language and package-manager coverage based on real-world feedback.
- [ ] Add more browser-native tools and contributor examples.

Features will be marked complete only when they are implemented, documented, and tested. The web tools are static browser utilities; the full web platform remains a future direction.

## Contributing

Contributions of all sizes are welcome—from reporting a confusing error message to improving documentation or implementing a tool.

Before opening a pull request:

1. Check existing issues to avoid duplicate work.
2. Describe the problem your change solves.
3. Include tests for new behavior where practical.
4. Update documentation when commands or behavior change.
5. Keep changes focused and avoid introducing unnecessary dependencies.

Contribution instructions will be expanded as the project structure takes shape. Please be respectful and constructive when interacting with other contributors.

## Community and support

- **Bug reports and feature ideas:** Use the repository's GitHub Issues.
- **Code contributions:** Open a Pull Request with a clear explanation and relevant tests.
- **Questions:** Start a GitHub Discussion when discussions are enabled.

## License

DevAid is intended to be released under the [MIT License](LICENSE). See the repository's license file for the exact terms.

---

<p align="center">
  Made for developers, by the open-source community.
  <br />
  <strong>Build better. Debug smarter. Ship confidently.</strong>
</p>