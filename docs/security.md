# DevAid Security Diagnostics

DevAid provides local, read-only security hygiene checks. Run:

```bash
devaid security .
devaid security-code .
devaid workflow-doctor .
devaid docker-doctor .
```

## Code scanner coverage

The static code scanner checks Python AST calls for dynamic evaluation, shell execution, unsafe pickle deserialization, YAML loading without an explicit loader, subprocess calls using `shell=True`, weak MD5/SHA-1 hashing, and potentially dynamic SQL query construction. JavaScript/TypeScript checks cover dynamic `eval`, `Function`, `innerHTML` assignment, and Node child-process `exec` calls.

## Safety and limitations

- Source code is read as text and is never executed or uploaded.
- Generated directories are excluded and file size/count limits bound scanning.
- Findings are heuristics, not proof of exploitability.
- A clean scan does not establish that a project is secure.
- Review context and use dedicated security tooling for production assurance.
- Never paste actual credentials into issue reports.
