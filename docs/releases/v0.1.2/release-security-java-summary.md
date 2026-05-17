# Image Security Summary: java

- image: `ghcr.io/senanayake/polyglot-devcontainers-java@sha256:691673ddf3d74d119a62620529e143d4cd4293de2b6fc563e1d07a8a4701fc85`

| Severity | Count |
| --- | ---: |
| Critical | 1 |
| High | 26 |
| Medium | 0 |
| Low | 0 |
| Fixable | 27 |
| Unfixed | 0 |
| Total | 27 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 24 | 1 | 23 | 24 |
| `jar` | 3 | 0 | 3 | 3 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 22 |
| `github.com/go-git/go-billy/v5` | 1 |
| `github.com/go-git/go-git/v5` | 1 |
| `org.bouncycastle:bcpg-jdk18on` | 1 |
| `org.bouncycastle:bcprov-jdk18on` | 1 |
| `org.codehaus.plexus:plexus-utils` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
