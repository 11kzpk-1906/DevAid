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

> **Project status:** DevAid is in its initial planning and development stage. The tools and commands listed below describe the intended roadmap; they are not claims of currently available functionality.

## Our goals

- **Free by design:** Keep the core experience usable without paid APIs or subscriptions.
- **Local-first:** Prefer running diagnostics on the developer's own machine.
- **Privacy-conscious:** Do not upload source code, logs, or project files without clear user consent.
- **Useful without AI:** Build deterministic tools first; make AI integrations optional.
- **Developer-friendly:** Support different experience levels, languages, and workflows.
- **Open to everyone:** Welcome contributions, feedback, bug reports, and ideas.

## Planned toolkit

| Tool | Purpose |
| --- | --- |
| Error Explainer | Turn confusing error messages into clearer explanations and troubleshooting guidance. |
| Project Analyzer | Inspect a project's structure, languages, frameworks, and common configuration issues. |
| Dependency Doctor | Review dependencies and highlight outdated, incompatible, or potentially problematic packages. |
| Deployment Doctor | Help investigate common build and deployment failures from logs supplied by the developer. |
| Security Checker | Run checks for common security problems using established, reputable tooling. |
| API Tester | Send HTTP requests and inspect responses. |
| Documentation Generator | Help create useful project documentation from available project information. |
| Environment Doctor | Identify common local development environment and configuration issues. |

The roadmap may change as we learn from developers and validate which problems matter most.

## Website + CLI

DevAid is planned as two connected experiences:

### Web platform
A clean, accessible home for DevAid tools, guides, documentation, and community resources. The initial site can be hosted as a static website to avoid requiring a paid backend.

### Command-line interface
A terminal-first companion designed to run diagnostics on a developer's machine. Example commands show the intended interface and are **illustrative only** until implemented:

```bash
# Explain an error log
devaid explain error.log

# Inspect the current project
devaid analyze .

# Review project dependencies
devaid deps

# Run common security checks
devaid security
```

## Technology direction

The initial implementation is expected to use:

- **Web:** React, TypeScript, and Tailwind CSS
- **CLI:** Python and Typer
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

The roadmap is intentionally incremental:

- [ ] Establish repository structure, contribution guidelines, and automated checks.
- [ ] Build the CLI foundation and a reliable command interface.
- [ ] Implement the first local tools: Error Explainer and Project Analyzer.
- [ ] Add Dependency Doctor.
- [ ] Publish the documentation website.
- [ ] Expand with Deployment Doctor, API Tester, and Environment Doctor.
- [ ] Add security checks and documentation generation.
- [ ] Gather community feedback and improve based on real-world use.

Features will be marked complete only when they are implemented, documented, and tested.

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
