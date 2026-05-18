---
id: KB-2026-074
type: failure-mode
status: active
created: 2026-05-17
updated: 2026-05-17
tags: [gitleaks, secret-scanning, ci, release-artifacts, sbom, memory-boundary]
related: [KB-2026-036, KB-2026-039, KB-2026-072]
---

# Gitleaks History Scan Large SBOM Memory Boundary

## Context

The root repository contract includes a final `gitleaks git .` history scan in
`task scan`. After v0.1.2 release-security evidence added large SPDX SBOM JSON
files under `docs/releases/v0.1.2/`, PR CI began failing in `ci-repo-core`.

## System/Component

- Root `Taskfile.yml`
- GitHub Actions `ci-repo-core`
- Maintainer-container `task scan`
- Gitleaks 8.30.1 Git history scan mode

## Failure Description

### Symptoms

- `ci-repo-core` fails during `task scan`.
- The failing command is the final repository-level `gitleaks git .` scan.
- The process exits with status `137` instead of reporting a secret finding.
- Path-scoped `gitleaks dir` scans continue to pass quickly.

### Failure Scenario

- GitHub Actions checks out the repository with the default shallow
  `fetch-depth: 1`.
- The repository contains large single-line generated SBOM JSON files.
- `gitleaks git .` runs with its default Git log options:
  `git -C . log -p -U0 --full-history --all --diff-filter=tuxdb`.
- Gitleaks attempts recursive decoding over very large patch segments.

### Impact

- A non-secret resource boundary blocks unrelated PRs.
- The security signal is noisy because the failure is a process kill, not a
  finding.
- The same boundary can reproduce locally in the maintainer container.

## Root Cause

### Primary Cause

Default Git-history scanning can feed very large generated SBOM patch content
into gitleaks' decoder pipeline. On memory-constrained runners and local
containers, that work can be killed with exit status `137`.

### Contributing Factors

- The release-security SBOM files are 15-39 MB each.
- They are minified single-line JSON, so a patch segment can be very large.
- Shallow CI checkouts make the checked-out commit appear as a shallow root, so
  the entire current tree is visible as one added patch.
- Gitleaks default decode depth is intentionally broad for normal source files.

### Failure Mechanism

```text
large minified SBOM files -> shallow-root Git patch -> gitleaks decoder scans
huge segments -> memory pressure -> process killed -> task scan exits 137
```

## Evidence

- Failed CI run:
  `https://github.com/senanayake/polyglot-devcontainers/actions/runs/26005249043/job/76435510616`
- CI log shows:
  `task: [scan] gitleaks git . --no-banner --redact --report-format sarif --report-path .artifacts/scans/gitleaks.sarif`
  followed by `task: Failed to run task "scan": exit status 137`.
- Local maintainer-container reproduction of unbounded `gitleaks git .` also
  exited `137`.
- A CI-style shallow clone with one commit reproduced the same `137`.
- Adding `--max-target-megabytes 10` completed successfully:
  `1 commits scanned`, `scanned ~156.54 MB`, `no leaks found`.

## Reproduction

### Minimal Reproduction Case

```bash
git clone --depth 1 --branch codex/windows-podman-support \
  https://github.com/senanayake/polyglot-devcontainers repro
cd repro
gitleaks git . --no-banner --redact \
  --report-format sarif \
  --report-path .artifacts/scans/gitleaks.sarif
```

### Conditions Required

- A shallow checkout containing the v0.1.2 release-security SBOM files.
- Gitleaks Git history scan without a maximum target size.
- Enough memory pressure for the decoder work to be killed.

## Prevention

### Design Changes

- Cap oversized targets in the root history scan with
  `--max-target-megabytes 10`.
- Keep normal source files, lockfiles, scripts, docs, and configuration within
  the history scan.
- Treat large generated release evidence as artifact evidence, not as generic
  source text for recursive secret decoding.

### Operational Controls

- Keep release-security SBOM generation out of the main source loop where
  practical, or format/chunk generated JSON if it must be committed.
- Use the maintainer container to reproduce scan failures before changing CI.

## Detection

### Early Warning Signs

- Newly committed generated files exceed 10 MB.
- Gitleaks debug output shows very large decoded `segment found` messages.
- `gitleaks git` exits `137` while `gitleaks dir` scans pass.

### Detection Methods

- Inspect failed CI logs around the final `task scan` command.
- Run a bounded and unbounded gitleaks comparison in the maintainer container.
- List large tracked files with `git ls-tree -r --long`.

## Mitigation

### Immediate Response

1. Reproduce the failing history scan inside the maintainer container.
2. Add a maximum target size to avoid decoder memory blow-ups on generated
   artifacts.
3. Re-run the failing scan and repository checks.

### Recovery Procedure

1. Push the bounded scan command.
2. Let PR CI re-run `ci-repo-core`.
3. If CI still fails, inspect whether another large generated file crosses the
   same boundary.

## Lessons Learned

- Git-history secret scanning needs resource bounds once generated evidence is
  committed to the repository.
- Shallow checkouts can turn the current tree into one giant root patch.
- Exit `137` should be treated as a resource boundary, not as a security
  finding.

## Applicability

### This Failure Mode Applies To

- Repositories with large generated JSON, SBOM, SARIF, or lock artifacts.
- Gitleaks Git history scans in shallow CI checkouts.
- Maintainer-container runs with constrained memory.

### This Failure Mode Does Not Apply To

- Normal source-code files below the target-size cap.
- Directory scans that do not process Git patch history.
- Actual secret findings reported by gitleaks.

## Status

- [x] Documented
- [x] Prevention implemented
- [x] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- KB-2026-036: Repo-History Gitleaks False Positive On GH CLI Key Fingerprints
- KB-2026-039: Template Gitleaks Scan Missed Root Ignore File
- KB-2026-072: Release Notes Summary Coverage Drift
