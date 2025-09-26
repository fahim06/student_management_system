# Dependency Audit Report (2025-09-26)

Scope: requirements.txt (PyPI)

Summary of dependencies, known vulnerabilities (from OSV), and available updates. Major updates are listed for batching
and may include breaking changes.

| Package       | Constraint      | Resolved (assumed) | Latest Compatible | Latest Overall | Update Type | Vulnerabilities |
|---------------|-----------------|-------------------:|------------------:|---------------:|-------------|-----------------|
| django        | ~=5.2           |              5.2.6 |             5.2.6 |          6.0a1 | patch       | None            |
| mysqlclient   | (unconstrained) |              2.2.7 |             2.2.7 |          2.2.7 | same        | None            |
| python-dotenv | ~=1.0           |              1.0.1 |             1.0.1 |          1.1.1 | same        | None            |
| pillow        | ~=10.3          |             10.3.0 |            10.3.0 |         11.3.0 | same        | None            |

## Notes

- Resolved versions assume a fresh install today that satisfies the specified constraints.
- Vulnerabilities are sourced from OSV.dev based on the resolved version.
- Patch/minor updates are generally safe; major updates may include breaking changes.

## Next steps

- You can choose to apply patch/minor updates where tests pass. Reply with approval to proceed.