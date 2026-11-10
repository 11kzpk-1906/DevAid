# Changelog

All notable changes to DevAid are documented here.

## [0.2.0] - 2026-11-08

### Added
- Local project snapshots with SHA-256 file fingerprints and comparison of added, modified, deleted, and unchanged files.
- Local project ZIP backups with common secret/cache exclusions, SHA-256 integrity verification, and safe restore into a new directory.
- `devaid update-check` checks the latest stable GitHub release without installing or changing files.
- Guided `devaid welcome` first-run menu for diagnostics, project analysis, dashboard, configuration, and help.
- Tests for the welcome flow and invalid project paths.

### Changed
- Promoted the v0.2.0 development line to the stable 0.2.0 release.

## [0.1.0] - 2026-11-02

### Added
- Offline-first developer diagnostics CLI.
- Full Doctor with 17 diagnostic reports.
- Project health, dependency, configuration, security,
  documentation, testing, and release-readiness checks.
- GitHub Actions workflow and Docker configuration checks.
- Interactive CLI dashboard.
- Custom diagnostic configuration through `.devaid.toml`.
- Third-party analyzer plugin architecture.
- Markdown, YAML, JSON, regex, and text-diff browser tools.
- GitHub repository health and README analysis tools.
- Changelog generation and Conventional Commit assistance.
- Environment, API response, dependency manifest,
  and Dockerfile analysis tools.
- Community issue templates and contributor documentation.

### Security and privacy
- Local, read-only diagnostic checks by default.
- Secret-aware checks that avoid printing environment values.
- Clear limitations for heuristic analysis tools.

### Notes
- Static diagnostics are guidance, not security guarantees.
- Browser tools that use external services disclose their limitations.
- Vulnerability database checks are not included in offline dependency analysis.