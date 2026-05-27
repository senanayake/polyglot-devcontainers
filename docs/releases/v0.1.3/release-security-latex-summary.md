# Image Security Summary: latex

- image: `ghcr.io/senanayake/polyglot-devcontainers-latex@sha256:a0d04b34f176f06c3f852d307c6567aa6de5e65a82c261b6dac43cd59c7bca5d`

| Severity | Count |
| --- | ---: |
| Critical | 2 |
| High | 23 |
| Medium | 0 |
| Low | 0 |
| Fixable | 25 |
| Unfixed | 0 |
| Total | 25 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 25 | 2 | 23 | 25 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 20 |
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
