---
id: KB-2026-072
type: failure-mode
status: active
created: 2026-05-17
updated: 2026-05-17
tags:
  - release
  - github-actions
  - published-images
  - release-notes
  - catalog
  - kbpd
related:
  - KB-2026-055
  - KB-2026-058
  - KB-2026-062
  - KB-2026-071
---

# Release Notes Summary Coverage Can Drift From Published Image Matrix

## Context

The `v0.1.1` release workflow successfully built, pushed, signed, attested, and
scanned all six published images:

- `polyglot-devcontainers-maintainer`
- `polyglot-devcontainers-java`
- `polyglot-devcontainers-diagrams`
- `polyglot-devcontainers-python-node`
- `polyglot-devcontainers-research-runner`
- `polyglot-devcontainers-latex`

The GitHub Release assets also included summary and SBOM files for all six
images. The release notes, however, showed only four images in the generated
Published Images and Security Status sections.

## System/Component

- `.github/workflows/release-images.yml`
- `scripts/build_release_security_summary.py`
- `published-image-catalog.toml`
- GitHub Release notes for full releases

## Failure Description

### Symptoms

- The release workflow run succeeds.
- Every image publish matrix job succeeds.
- Release assets include `latex` and `research-runner` security summaries and
  SBOMs.
- The release notes omit `latex` and `research-runner`.
- The security totals in the release notes are lower than the actual full-image
  scan totals.

### Failure Scenario

- The release matrix is generated from `published-image-catalog.toml`.
- The first release-security summary step passes all six image summaries.
- A later release-note update step rebuilds the same release-security block but
  passes only four hard-coded `--summary` arguments.
- The second generated block replaces the complete block in the release notes.

### Impact

- The release page gives an incomplete public view of published images.
- The release security table omits real scan results for images that were
  published and attached as assets.
- Users cannot rely on release notes as a complete image inventory.
- The workflow can pass while publishing incomplete release documentation.

## Root Cause

### Primary Cause

Release-note generation duplicated the image summary list instead of deriving
it from the same catalog-driven image matrix. The duplicated list was not
updated when `latex` and `research-runner` were added.

### Contributing Factors

- The image build path was catalog-driven, but the final release-note update
  path still had a hard-coded summary argument list.
- The workflow had no check that every catalog image appears in every
  `build_release_security_summary.py` invocation.
- Success of the publish jobs masked the documentation drift.
- Release docs publishing had a separate untracked-file detection bug:
  `git diff --quiet` ran before `git add`, so newly created `docs/releases/*`
  files were treated as "already up to date."

### Failure Mechanism

```text
catalog contains six images
-> publish matrix builds six images
-> prepare-release-security generates complete six-image summary
-> publish-release-security rebuilds notes from four hard-coded summaries
-> four-image block replaces complete release-note block
-> release notes under-report the published image set
```

## Evidence

GitHub Actions run `25982061103` for release `v0.1.1`:

- six `publish (...)` jobs completed successfully
- release assets included:
  - `release-security-latex-summary.json`
  - `release-security-latex-sbom.spdx.json`
  - `release-security-research-runner-summary.json`
  - `release-security-research-runner-sbom.spdx.json`
- the release notes listed only:
  - `polyglot-devcontainers-diagrams`
  - `polyglot-devcontainers-java`
  - `polyglot-devcontainers-maintainer`
  - `polyglot-devcontainers-python-node`

Workflow inspection showed that `prepare-release-security` passed all six
summary files, while `publish-release-security` passed only four.

## Prevention

### Design Changes

- Keep release-note image coverage tied to `published-image-catalog.toml`.
- Check release workflow summary coverage against catalog artifact names.
- Avoid duplicating image summary lists across jobs when possible.
- When committing generated docs, stage the target path before checking whether
  there is a diff so untracked release docs are detected.

### Operational Controls

- After a full release, compare:
  - publish matrix job count
  - release asset summary file count
  - Published Images section count
  - Security Status table count
- Treat mismatches as release-documentation failures even if image publication
  succeeded.

## Detection

### Early Warning Signs

- `published-image-catalog.toml` changes without corresponding workflow summary
  coverage changes.
- Release assets and release-note tables have different image counts.
- A release docs job says "already up to date" immediately after creating a new
  `docs/releases/<tag>` directory.

### Detection Methods

- `scripts/check.py --workspace .` now checks that every published image
  artifact name appears in each release summary command in
  `.github/workflows/release-images.yml`.
- Manual release review can compare package assets against the generated notes.

## Mitigation

### Immediate Response

1. Add the missing `latex` and `research-runner` summaries to the
   release-note update step.
2. Fix the release docs commit step to run `git add` before
   `git diff --cached --quiet`.
3. Add a repository check to prevent future catalog/workflow coverage drift.
4. Regenerate or edit the affected release notes if the existing release page
   must be corrected before the next release.

## Lessons Learned

- A catalog-driven build matrix is not enough if downstream reporting still
  duplicates catalog state.
- Release documentation needs the same completeness checks as release
  publication.
- Successful image publication can still produce an incomplete release if the
  evidence aggregation path is not covered.
- Generated release docs must account for untracked files, not only changes to
  already tracked paths.

## Applicability

### This Failure Mode Applies To

- Full release workflows that publish multiple images.
- Release notes generated from security summary artifacts.
- Any workflow where the build matrix is dynamic but reporting inputs are
  hard-coded.

### This Failure Mode Does Not Apply To

- Single-image release workflows with no generated summary aggregation.
- Source-only validation lanes.

## Status

- [x] Documented
- [x] Prevention implemented for summary coverage
- [x] Detection implemented in `scripts/check.py`
- [x] Release docs untracked-file detection fixed
- [ ] Affected `v0.1.1` release notes regenerated

## Related Knowledge

- [KB-2026-055](KB-2026-055-free-tier-image-validation-should-use-fast-medium-and-full-release-lanes.md)
- [KB-2026-058](KB-2026-058-full-release-validation-and-release-publication-still-need-a-single-build-gate.md)
- [KB-2026-062](KB-2026-062-mainline-full-release-evidence-should-gate-cut-release-and-publication.md)
- [KB-2026-071](KB-2026-071-windows-podman-image-validation-storage-exhaustion.md)
