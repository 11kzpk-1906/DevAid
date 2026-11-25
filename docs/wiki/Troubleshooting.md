# Troubleshooting

- If a command is unavailable, check `devaid --help` and confirm the installed version with `devaid version`.
- If a standalone executable is not found, run it from the extracted folder.
- If a backup fails verification, create a new backup and keep the original archive unchanged.
- If coverage data is unavailable, generate a coverage.py JSON or XML report first.
- If a plugin fails, verify its entry-point name, API version, and manifest. Third-party plugin code runs with your permissions.
- For reproducible bugs, open a GitHub issue with the command, operating system, DevAid version, and redacted output. Never attach secrets.
