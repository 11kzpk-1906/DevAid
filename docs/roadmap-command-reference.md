# DevAid roadmap command reference

These commands are local-first. They do not upload project files.

| Command | Purpose |
| --- | --- |
| `devaid sbom --path PATH --format cyclonedx --output bom.json` | Generate CycloneDX 1.5 JSON; use `--format spdx` for SPDX 2.3. Existing output is protected unless `--overwrite` is passed. |
| `devaid secret-scan --path PATH` | Find selected credential patterns. Values are never included in findings. |
| `devaid sarif --path PATH --output results.sarif` | Export supported secret findings as SARIF 2.1.0. |
| `devaid licenses --path PATH` | Inventory dependencies declared in supported manifests; unknown license data is explicitly marked. |
| `devaid git-review --path PATH` | Review staged and unstaged Git file changes without modifying the repository. |
| `devaid coverage --path PATH` | Read existing coverage.py JSON or XML reports. Optional `--run-tests` explicitly runs pytest under coverage.py with a fixed argument list and timeout. |
| `devaid history --path PATH --output .devaid/history/run.json` | Save a local metadata-only project snapshot with a transparent six-check health score and redacted finding metadata. |
| `devaid history-compare BEFORE AFTER` | Compare two versioned history snapshots, scores, and new/resolved/unchanged findings. |
| `devaid explore --path PATH --depth 2` | Display a terminal-friendly project tree. |

## Limitations

- SBOM extraction currently reads `pyproject.toml`, `requirements.txt`, and `package.json`. It reads npm package-lock entries (including resolved transitive packages) and Poetry lock entries. A limited set of explicitly declared SPDX licenses is retained; other values remain unknown.
- Secret scanning uses bounded local pattern checks, honors `.gitignore` and `[security].exclude` patterns in `.devaid.toml`, and includes low-confidence entropy candidates. It cannot guarantee detection. Findings contain no matched values.
- SARIF export currently covers secret-scanner rules; other diagnostics can be added as schemas stabilize.
- License inventory reports only a limited allowlist of recognized SPDX identifiers from package-lock and Poetry lock metadata; other values remain unknown. Configure `[licenses] deny = ["GPL-3.0-only"]` or an optional `allow` list in `.devaid.toml` to flag packages for review. It is not legal advice.
- Git review reports changed file names and basic sensitive/generated-file heuristics; it cannot prove a change safe or unsafe.
- Coverage reads existing `coverage.json` or `coverage.xml` by default. `--run-tests` is explicit opt-in to execute pytest under coverage.py with a 300-second timeout.
- History snapshots contain timestamps, version, and aggregate file counts, not source code or environment values.
- The explorer offers a numbered, keyboard-operated directory navigator in interactive terminals and falls back to a static tree in CI or non-interactive terminals. It does not execute project code or modify files.

## Analyzer plugin SDK

Third-party analyzers use the `devaid.analyzers` Python entry-point group. New SDK plugins should ship a `devaid-plugin.toml` file containing `[devaid-plugin]`, `name`, `api-version = 1`, and `entry-point = "package.module:callable"`. DevAid validates that manifest before importing plugin code. Each callback accepts one `pathlib.Path`; the SDK exposes immutable `AnalyzerFinding` and `AnalyzerResult` data contracts. Older entry-point-only plugins remain supported for compatibility. Listing plugins reads metadata and does not import plugin modules. Running a plugin is explicit and executes third-party Python code with the current user's permissions; install and run only trusted plugins. This SDK is not a sandbox.