# Image Security Summary: python-node

- image: `ghcr.io/senanayake/polyglot-devcontainers-python-node@sha256:76d6f85baf889012add0feef6dba7ad1237e574f3f6b2f1dfda512d028d4f881`

| Severity | Count |
| --- | ---: |
| Critical | 1 |
| High | 43 |
| Medium | 0 |
| Low | 0 |
| Fixable | 44 |
| Unfixed | 0 |
| Total | 44 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 17 | 1 | 16 | 17 |
| `node-pkg` | 14 | 0 | 14 | 14 |
| `python-pkg` | 13 | 0 | 13 | 13 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 17 |
| `tar` | 6 |
| `GitPython` | 5 |
| `jaraco.context` | 3 |
| `minimatch` | 3 |
| `pnpm` | 3 |
| `wheel` | 3 |
| `black` | 1 |
| `glob` | 1 |
| `picomatch` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
