# Image Security Summary: maintainer

- image: `ghcr.io/senanayake/polyglot-devcontainers-maintainer@sha256:524c91ea5b1fce99dbbed881fc7eadc98190ef789a22a0fca810f74ab4d226a4`

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 72 |
| Medium | 0 |
| Low | 0 |
| Fixable | 74 |
| Unfixed | 0 |
| Total | 74 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 44 | 2 | 42 | 44 |
| `jar` | 3 | 0 | 3 | 3 |
| `node-pkg` | 14 | 0 | 14 | 14 |
| `python-pkg` | 13 | 0 | 13 | 13 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 41 |
| `tar` | 6 |
| `GitPython` | 5 |
| `jaraco.context` | 3 |
| `minimatch` | 3 |
| `pnpm` | 3 |
| `wheel` | 3 |
| `black` | 1 |
| `github.com/go-git/go-billy/v5` | 1 |
| `github.com/go-git/go-git/v5` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.6` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
