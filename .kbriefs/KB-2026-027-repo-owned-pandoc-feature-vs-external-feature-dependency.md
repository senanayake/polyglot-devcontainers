---
id: KB-2026-027
type: tradeoff
status: validated
created: 2026-04-24
updated: 2026-04-24
tags: [kbpd, tradeoff, features, pandoc, documentation, devcontainers]
related: [KB-2026-014, KB-2026-025]
---

# Repo-Owned Pandoc Feature vs External Feature Dependency

## Context

Polyglot needed a reusable document-rendering capability for Markdown to HTML
and PDF workflows. The repository already ships a small feature library and
prefers composable, repo-owned building blocks over large custom images.

## Question/Problem

Should Polyglot consume an existing community Pandoc devcontainer feature or
add a repo-owned `pandoc` feature to its own feature library?

## Investigation

We reviewed:
- the repository feature strategy in `AGENTS.md`
- the current repo feature library shape under `features/`
- the public Dev Container Features registry on `containers.dev`

The registry currently lists community-maintained Pandoc features, including
entries from Rocker Project and devcontainers-extra.

## Findings

- Existing community Pandoc features already exist, so this capability is not a
  greenfield gap in the broader devcontainer ecosystem.
- A repo-owned Pandoc feature still fits Polyglot when the goal is a minimal,
  predictable substrate capability that matches the repository's other
  feature-install patterns.
- The key control point is optionality: Pandoc alone is lightweight enough for
  a general document tool, while TeX support is materially heavier and should
  remain opt-in.
- The maintenance burden is acceptable because the implementation can stay
  distro-native and small: `apt-get install pandoc`, with optional
  `texlive-latex-recommended` and `texlive-xetex`.

## Evidence

- `AGENTS.md` directs agents to prefer existing features first, but also allows
  repo-owned features when necessary for secure, composable workflows.
- `features/` currently favors small, explicit install surfaces over opaque
  external indirection.
- The public features registry currently lists community Pandoc features rather
  than a repo-native Polyglot one.

## Implications

- Polyglot can add `features/pandoc/` without violating its simplicity goals as
  long as the feature remains narrow and optional-heavy dependencies stay off by
  default.
- Documentation must include the new feature so downstream users can discover
  it as part of the repo-owned feature library.
- Templates do not need to consume the feature immediately; it can remain an
  available building block until a starter proves the need.

## Recommendations

- Prefer a repo-owned Pandoc feature when document rendering is a reusable
  substrate capability for multiple downstream workspaces.
- Keep the default install to `pandoc` only.
- Gate LaTeX-backed PDF generation behind an explicit `texlive` option.
- Reevaluate the choice if an upstream official feature becomes a better fit
  than the repo-owned maintenance cost.

## Applicability

Applies when:
- the repository wants a stable, documented document-rendering primitive
- downstream consumers benefit from a repo-owned, auditable install path
- optional heavyweight dependencies can be clearly isolated

Does not apply when:
- a downstream project is happy to depend directly on a third-party feature
- the capability is one-off and not worth adding to the shared feature library
