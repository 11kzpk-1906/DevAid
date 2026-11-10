# DevAid Security Diagnostics

DevAid provides local, read-only security hygiene checks. Run:

```bash
devaid security .
devaid security-code .
devaid workflow-doctor .
devaid docker-doctor .
```

## Secret and Git exposure checks

`devaid security .` scans supported text files for common credential patterns, including private-key headers, AWS access-key IDs, GitHub tokens, and credential assignments. It redacts detected values in its output.

It also checks whether Git currently tracks sensitive-looking paths such as `.env`, common private-key files, credential JSON files, and certificate/key bundles. This check uses a fixed, read-only `git ls-files` command; it does not modify the repository. A file ignored today may still be tracked if it was added before the ignore rule.

If a real credential has been committed, removing the file in a later commit is not enough: revoke or rotate the credential, then follow your repository's secret-removal process. Do not paste real secrets into issues or logs.

## Code scanner coverage

The static code scanner checks Python AST calls for dynamic evaluation, shell execution, unsafe pickle deserialization, YAML loading without an explicit loader, subprocess calls using `shell=True`, weak MD5/SHA-1 hashing, and potentially dynamic SQL query construction. JavaScript/TypeScript checks cover dynamic `eval`, `Function`, `innerHTML` assignment, and Node child-process `exec` calls.

## Safety and limitations

- Source code is read as text and is never executed or uploaded.
- Git inspection is read-only and uses argument-list subprocess calls without a shell.
- Generated directories are excluded and file size/count limits bound scanning.
- Findings are heuristics, not proof of exploitability; false positives and missed issues are possible.
- A clean scan does not establish that a project is secure.
- Dependency manifest inspection is offline and does not identify known vulnerable package versions.
- Review context and use dedicated security tooling for production assurance.
