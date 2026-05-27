# Image Security Summary: maintainer

- image: `ghcr.io/senanayake/polyglot-devcontainers-maintainer@sha256:b8f74025e7b5c255389a15d83109897fe3c08039e2156f35611513674bbc53f1`

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 82 |
| Medium | 0 |
| Low | 0 |
| Fixable | 84 |
| Unfixed | 0 |
| Total | 84 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 54 | 2 | 52 | 54 |
| `jar` | 3 | 0 | 3 | 3 |
| `node-pkg` | 14 | 0 | 14 | 14 |
| `python-pkg` | 13 | 0 | 13 | 13 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 49 |
| `tar` | 6 |
| `GitPython` | 5 |
| `jaraco.context` | 3 |
| `minimatch` | 3 |
| `pnpm` | 3 |
| `wheel` | 3 |
| `black` | 1 |
| `github.com/containerd/containerd` | 1 |
| `github.com/containerd/containerd/v2` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.6` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
