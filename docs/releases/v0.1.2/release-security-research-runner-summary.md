# Image Security Summary: research-runner

- image: `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:3cbfbed6dd91dfeddbcfa22fc0a425857f6b7daee68992442623a83dbc49cb20`

| Severity | Count |
| --- | ---: |
| Critical | 1 |
| High | 71 |
| Medium | 0 |
| Low | 0 |
| Fixable | 72 |
| Unfixed | 0 |
| Total | 72 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `debian` | 28 | 0 | 28 | 28 |
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
| `libpython3.11-minimal` | 3 |
| `libpython3.11-stdlib` | 3 |
| `minimatch` | 3 |
| `openssh-client` | 3 |
| `pnpm` | 3 |
| `python3.11` | 3 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
