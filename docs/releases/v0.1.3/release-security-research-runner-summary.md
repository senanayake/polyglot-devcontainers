# Image Security Summary: research-runner

- image: `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a`

| Severity | Count |
| --- | ---: |
| Critical | 11 |
| High | 81 |
| Medium | 0 |
| Low | 0 |
| Fixable | 92 |
| Unfixed | 0 |
| Total | 92 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `debian` | 49 | 10 | 39 | 49 |
| `gobinary` | 16 | 1 | 15 | 16 |
| `node-pkg` | 14 | 0 | 14 | 14 |
| `python-pkg` | 13 | 0 | 13 | 13 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 16 |
| `tar` | 6 |
| `GitPython` | 5 |
| `libgnutls-dane0` | 5 |
| `libgnutls-openssl27` | 5 |
| `libgnutls28-dev` | 5 |
| `libgnutls30` | 5 |
| `libgnutlsxx30` | 5 |
| `jaraco.context` | 3 |
| `minimatch` | 3 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2026-33845` | `libgnutls-dane0` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-42010` | `libgnutls-dane0` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-33845` | `libgnutls-openssl27` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-42010` | `libgnutls-openssl27` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-33845` | `libgnutls28-dev` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-42010` | `libgnutls28-dev` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-33845` | `libgnutls30` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-42010` | `libgnutls30` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-33845` | `libgnutlsxx30` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2026-42010` | `libgnutlsxx30` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `debian` |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
