---
id: KB-2026-042
type: standard
status: published
created: 2026-04-29
updated: 2026-04-29
tags: [starters, images, bootstrap, proof, kbpd]
related:
  - KB-2026-039-retry-upstream-binary-downloads-in-image-builds.md
  - KB-2026-041-generated-starter-scenario-proof-should-run-in-the-generated-workspace.md
---

# Image-Backed Starter Proof Should Use Branch-Local Verify Images

## Context

The starter catalog now supports `published-image-bootstrap` generation, but
proofing that path against GHCR `:main` images can drift from the current
branch state. The branch may have a stronger scaffold contract than the last
published image, especially while image and starter work are evolving together.

## Decision

Use branch-local `:verify` images for image-backed starter proofing whenever
the goal is to validate the current branch contract.

Keep generated `.devcontainer/devcontainer.json` output pointed at the stable
published image reference, but allow the proof harness to override the runtime
image it exercises.

## Why This Is The Right Standard Now

- it separates user-facing starter output from branch-local proof infrastructure
- it avoids false failures caused by stale published images
- it keeps the bootstrap path honest by validating the exact image definitions
  built from current source

## Evidence

- image-backed starter proof initially failed against GHCR `:main` images even
  though the generated seed workspace was correct
- the same proof passed once `task image:build` produced local
  `polyglot-devcontainers-*:verify` images and the starter proof harness used
  those image refs
- the maintainer-container `starters:verify:image-backed` lane now builds local
  verify images, then proves the Java and Python/Node bootstrap paths against
  those local images

## Applicability

### This Standard Applies To

- branch validation for image-backed starter generation
- CI lanes that need to prove current-source image behavior

### This Standard Does Not Apply To

- downstream user documentation, which should keep pointing at published image
  refs
- release validation after the branch images have already been published and
  are expected to be authoritative
