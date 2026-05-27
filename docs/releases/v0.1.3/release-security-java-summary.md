# Image Security Summary: java

- image: `ghcr.io/senanayake/polyglot-devcontainers-java@sha256:ca77d9610aa52d1324cde853a7be93722f690a19c4d715e59229052780f282ec`

| Severity | Count |
| --- | ---: |
| Critical | 1 |
| High | 27 |
| Medium | 0 |
| Low | 0 |
| Fixable | 28 |
| Unfixed | 0 |
| Total | 28 |

## By type

| Type | Total | Critical | High | Fixable |
| --- | ---: | ---: | ---: | ---: |
| `gobinary` | 25 | 1 | 24 | 25 |
| `jar` | 3 | 0 | 3 | 3 |

## Top packages

| Package | Findings |
| --- | ---: |
| `stdlib` | 21 |
| `github.com/containerd/containerd` | 1 |
| `github.com/containerd/containerd/v2` | 1 |
| `github.com/go-git/go-billy/v5` | 1 |
| `github.com/go-git/go-git/v5` | 1 |
| `org.bouncycastle:bcpg-jdk18on` | 1 |
| `org.bouncycastle:bcprov-jdk18on` | 1 |
| `org.codehaus.plexus:plexus-utils` | 1 |

## Critical CVEs

| CVE | Package | Installed | Fixed | Type |
| --- | --- | --- | --- | --- |
| `CVE-2025-68121` | `stdlib` | `v1.24.11` | `1.24.13, 1.25.7, 1.26.0-rc.3` | `gobinary` |
