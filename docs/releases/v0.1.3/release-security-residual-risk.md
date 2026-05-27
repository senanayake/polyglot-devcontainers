# Residual Risk Report

- critical findings: `20`

| Classification | Count |
| --- | ---: |
| `review_required` | 10 |
| `upstream_residual` | 10 |

## Critical findings

| Image | Classification | Action | Target | Package | CVE | Installed | Fixed | Upstream release source |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `diagrams` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/d2` | `stdlib` | `CVE-2025-68121` | `v1.24.6` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `terrastruct/d2` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `diagrams` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `java` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `latex` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `latex` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/libexec/polyglot-devcontainers/task-real` | `google.golang.org/grpc` | `CVE-2026-33186` | `v1.76.0` | `1.79.3` | `go-task/task` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `maintainer` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/d2` | `stdlib` | `CVE-2025-68121` | `v1.24.6` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `terrastruct/d2` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `maintainer` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `python-node` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `research-runner` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `solver-runner` | `upstream_residual` | `wait_for_upstream_release` | `usr/local/bin/gitleaks` | `stdlib` | `CVE-2025-68121` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gitleaks/gitleaks` |

Rationale: Latest upstream-supported release is in use for this managed binary; track the finding and wait for the vendor to publish a refreshed release.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls-dane0` | `CVE-2026-33845` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls-dane0` | `CVE-2026-42010` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls-openssl27` | `CVE-2026-33845` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls-openssl27` | `CVE-2026-42010` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls28-dev` | `CVE-2026-33845` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls28-dev` | `CVE-2026-42010` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls30` | `CVE-2026-33845` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutls30` | `CVE-2026-42010` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutlsxx30` | `CVE-2026-33845` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

| `research-runner` | `review_required` | `fix_in_repo_or_investigate` | `ghcr.io/senanayake/polyglot-devcontainers-research-runner@sha256:a9dc31c2acdaa2779b2a9435ad2034cb3a6c33f0efb95ff9d2b2933e202b6b7a (debian 12.13)` | `libgnutlsxx30` | `CVE-2026-42010` | `3.7.9-2+deb12u6` | `3.7.9-2+deb12u7` | `` |

Rationale: Finding is not covered by the upstream-managed binary policy and requires repository-side remediation or manual investigation.

