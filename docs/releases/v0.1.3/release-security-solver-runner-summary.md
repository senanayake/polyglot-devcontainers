# Image Security Summary: solver-runner

- image: `ghcr.io/senanayake/polyglot-devcontainers-solver-runner@sha256:c025726656e5890e9838d921c7215d24aa15b6c4466c9293390b427f86dbc905`

| Severity | Count |
| --- | ---: |
| Critical | 1 |
| High | 42 |
| Medium | 0 |
| Low | 0 |
| Fixable | 43 |
| Unfixed | 0 |
| Total | 43 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 16 | 1 | 15 | 16 |
| `node-pkg` | 14 | 0 | 14 | 14 |
| `python-pkg` | 13 | 0 | 13 | 13 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 16 |
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
