---
id: KB-2026-012
type: pattern
status: active
created: 2026-04-12
updated: 2026-04-12
tags: [diagrams, consumer, starter, devcontainer, release-tags, usability]
related: [KB-2026-010, KB-2026-011]
---

# Diagram Consumer Starter Contract: Pin Real Image Tags and Ship Source Files

## Context

A downstream repo at `C:\dev\diagrams` was created to consume the published
diagrams image through a direct `"image"` reference.

The initial repo contained only:

- `.devcontainer/devcontainer.json`
- `.artifacts/`

The user then tried to render:

```bash
diagram render --tool d2 --input docs/diagrams/example.d2 --output .artifacts/diagrams/example.svg --manifest .artifacts/diagrams/example.json
```

## Problems

Two separate consumer-readiness failures appeared.

### Problem 1: Floating `:main` Tag Assumption

The consumer devcontainer referenced:

```json
"image": "ghcr.io/senanayake/polyglot-devcontainers-diagrams:main"
```

But the published diagrams image did not have a `:main` manifest available for
pull at the time of testing. The actual working image was:

```text
ghcr.io/senanayake/polyglot-devcontainers-diagrams:v0.0.25
```

### Problem 2: Empty Workspace

The container was usable, but the workspace had no source files under
`docs/diagrams/`, so the render command failed correctly with:

```text
open /workspaces/diagrams/docs/diagrams/example.d2: no such file or directory
```

## Decision

A usable downstream diagram consumer must satisfy both conditions:

1. Pin an actually published image tag such as `v0.0.25`
2. Include diagram source files, not only devcontainer metadata

## Minimum Starter Contract

The minimum viable consumer repo should include:

```text
.devcontainer/devcontainer.json
.gitignore
README.md
Taskfile.yml
docs/diagrams/example.d2
```

For the CVE presentation use case, it should also include:

```text
docs/diagrams/cve-portfolio/direct-vs-transitive.d2
docs/diagrams/cve-portfolio/vulnerability-emergence-direct.d2
docs/diagrams/cve-portfolio/vulnerability-emergence-transitive.d2
```

## Rationale

### Version Pinning

Consumers need deterministic pull targets. A release tag is a real contract.
Assuming a floating `:main` tag exists is weaker and can break silently.

### Source-Complete Starters

A repo that only defines the runtime is not a usable starter. A starter must
contain at least one renderable input at the documented path.

If the first documented example is:

```bash
diagram render --tool d2 --input docs/diagrams/example.d2 ...
```

then `docs/diagrams/example.d2` must exist.

### Task Contract

The diagram consumer also benefits from a lightweight task surface:

- `task init`
- `task lint`
- `task render`
- `task test`
- `task scan`
- `task ci`

This gives both humans and agents a predictable execution loop.

## Applied Outcome

The local consumer repo was corrected by:

- pinning the devcontainer image to `ghcr.io/senanayake/polyglot-devcontainers-diagrams:v0.0.25`
- adding a smoke-test `docs/diagrams/example.d2`
- adding the three initial CVE portfolio diagrams
- adding a `Taskfile.yml`, `.gitignore`, and `README.md`

## Implications

- Downstream examples should be distributed as complete starters, not bare
  image references.
- Published documentation should avoid assuming `:main` exists unless the
  release workflow explicitly guarantees it.
- The first documented command in a starter must be executable as written.
