# Image Security Summary: latex

- image: `ghcr.io/senanayake/polyglot-devcontainers-latex@sha256:8a46471ffd1fb2acbb703ea1d791e05cc236ef2e393b5519e29f58e8cbd335a7`

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 24 |
| Medium | 0 |
| Low | 0 |
| Fixable | 26 |
| Unfixed | 0 |
| Total | 26 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 26 | 2 | 24 | 26 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 21 |
| `github.com/go-jose/go-jose/v4` | 1 |
| `github.com/hashicorp/go-getter` | 1 |
| `go.opentelemetry.io/otel` | 1 |
| `go.opentelemetry.io/otel/sdk` | 1 |
| `google.golang.org/grpc` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2026-33186` | `google.golang.org/grpc` | `v1.76.0` | `1.79.3` | `gobinary` |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
