# DevAid roadmap command reference

These commands are local-first. They do not upload project files.

| Command | Purpose |
| --- | --- |
| `devaid sbom PATH --format cyclonedx --output bom.json` | Generate CycloneDX 1.5 JSON; use `--format spdx` for SPDX 2.3. Existing output is protected unless `--overwrite` is passed. |
| `devaid secret-scan PATH` | Find selected credential patterns. Values are never included in findings. |
| `devaid sarif PATH --output results.sarif` | Export supported secret findings as SARIF 2.1.0. |
| `devaid licenses PATH` | Inventory dependencies declared in supported manifests; unknown license data is explicitly marked. |
| `devaid git-review PATH` | Review staged and unstaged Git file changes without modifying the repository. |
| `devaid coverage PATH` | Read existing coverage.py JSON or XML reports; never runs tests. |
| `devaid history PATH --output .devaid/history/run.json` | Save a local metadata-only project snapshot. |
| `devaid history-compare BEFORE AFTER` | Compare two versioned history snapshots. |
| `devaid explore PATH --depth 2` | Display a terminal-friendly project tree. |

## Limitations

- SBOM extraction currently reads `pyproject.toml`, `requirements.txt`, and `package.json`. It does not resolve transitive dependencies or infer license metadata.
- Secret scanning uses bounded local pattern checks and cannot guarantee detection. Findings contain no matched values.
- SARIF export currently covers secret-scanner rules; other diagnostics can be added as schemas stabilize.
- License inventory deliberately reports unknown metadata instead of guessing. It is not legal advice.
- Git review reports changed file names and basic sensitive/generated-file heuristics; it cannot prove a change safe or unsafe.
- Coverage reads existing `coverage.json` or `coverage.xml`; it never executes project code.
- History snapshots contain timestamps, version, and aggregate file counts, not source code or environment values.
- The explorer is a static tree view, not an interactive TUI. It is safe in CI and non-interactive terminals.

## Analyzer plugin SDK

Third-party analyzers use the `devaid.analyzers` Python entry-point group. Each entry point resolves to a callable accepting one `pathlib.Path`. Listing plugins reads metadata and does not import plugin modules. Running a plugin is explicit and executes third-party Python code with the current user's permissions; install and run only trusted plugins. This minimal entry-point contract is not a sandbox.