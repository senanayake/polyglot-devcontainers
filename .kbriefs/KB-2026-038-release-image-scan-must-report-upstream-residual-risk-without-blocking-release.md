---
id: KB-2026-038
type: failure-mode
status: published
created: 2026-04-26
updated: 2026-04-26
tags: [release, images, trivy, residual-risk, upstream-binaries]
related:
  - KB-2026-013-risk-driven-cve-management.md
  - KB-2026-014-cve-inflow-reduction-and-maintenance-economics.md
---

# Release Image Scan Must Report Upstream Residual Risk Without Blocking Release

## Context

The release workflow publishes four devcontainer images and then scans the published digests with Trivy. This repository intentionally ships some upstream-managed binaries such as `task`, `gitleaks`, and `d2`. Those binaries can carry scanner findings that are not remediable in-repo when the latest upstream-supported release is already in use.

## System/Component

- `.github/workflows/release-images.yml`
- `scripts/build_residual_risk_report.py`
- published images built from `.devcontainer/Containerfile` and `templates/*/.devcontainer/Containerfile`

## Failure Description

### Symptoms

- `release-images` fails at `Scan published image with Trivy (SARIF)`
- image build, push, signing, and attestation all succeed, but the workflow still ends in failure
- downstream full releases do not publish release notes and security artifacts because the publish matrix never completes successfully

### Failure Scenario

- an image contains `HIGH` or `CRITICAL` findings in upstream-managed binaries
- the workflow runs `aquasecurity/trivy-action` with its default non-zero exit behavior
- findings that should be documented as residual risk instead abort the release pipeline

### Impact

- valid releases are blocked even when the repo is already on the latest upstream-supported binary release
- residual-risk reporting steps never run, so the release loses the documentation path that policy requires
- `cut-release` appears broken even though the actual defect is the scan gate behavior

## Root Cause

### Primary Cause

The release workflow treated Trivy findings as a hard gate before the workflow had a chance to classify them under the repository's upstream-managed binary policy.

### Contributing Factors

- `scripts/build_residual_risk_report.py` classified `task` and `gitleaks`, but not `d2`
- the SARIF and JSON Trivy actions scanned for vulnerabilities but were not configured with `exit-code: 0`
- published-image release steps ran before residual-risk documentation could be generated

### Failure Mechanism

```
latest upstream binary still has CVEs -> Trivy exits non-zero -> publish matrix fails
-> residual-risk docs are skipped -> full release fails
```

## Evidence

- GitHub Actions run `24949589052` failed on the `diagrams` publish job after build, push, sign, and attestation completed
- local reproduction of the diagrams image scan showed no Debian OS findings, but did show `HIGH`/`CRITICAL` findings in `d2`, `gitleaks`, and `task`
- the current repository policy in `AGENTS.md` says latest upstream-supported binary releases should be documented as upstream residual risk rather than privately patched or replaced

## Reproduction

### Minimal Reproduction Case

```bash
task image:build
trivy image --input .artifacts/images/diagrams.tar --severity HIGH,CRITICAL --ignore-unfixed --scanners vuln --pkg-types os,library --format table
```

### Conditions Required

- published image contains upstream-managed Go binaries
- Trivy scan runs on the published digest or saved image tarball
- workflow treats scanner findings as fatal before policy classification

## Prevention

### Design Changes

- run release-image Trivy steps with `exit-code: 0`
- keep vulnerability scanning enabled and upload SARIF/JSON artifacts
- classify upstream-managed binaries explicitly in `scripts/build_residual_risk_report.py`, including `d2`

### Operational Controls

- update vendored binaries to the latest upstream-supported release before cutting a release
- treat remaining findings as residual risk only after verifying the image already uses the latest upstream release
- review release security artifacts as part of the release acceptance decision

### Monitoring

- watch release-security summary artifacts for new `review_required` critical findings
- monitor the count of upstream residual findings across releases
- track upstream release feeds for `go-task/task`, `gitleaks/gitleaks`, and `terrastruct/d2`

## Detection

### Early Warning Signs

- Trivy publish steps fail after successful image pushes
- release artifacts are missing even though image digests were published
- summary tables show findings only in vendored binaries, not in OS packages

### Detection Methods

- inspect `release-images` workflow logs
- run local `task image:build` plus a focused Trivy scan on the affected image tarball
- inspect residual-risk JSON and markdown outputs

## Mitigation

### Immediate Response

1. Confirm the failing findings belong to upstream-managed binaries rather than repo-owned packages.
2. Update binary pins to the latest upstream-supported releases where newer versions exist.
3. Reconfigure release scanning so findings are reported and summarized instead of terminating the workflow.

### Recovery Procedure

1. Patch the workflow to continue past Trivy findings.
2. Expand residual-risk classification for the affected binaries.
3. Re-run the release workflow and verify release security assets are published.

### Graceful Degradation

- allow release completion with residual-risk artifacts when the latest upstream release still carries findings
- keep `review_required` findings visible so true repo-owned vulnerabilities still stand out in the reports

## Testing

### Test Cases

```bash
task image:build
trivy image --input .artifacts/images/diagrams.tar --severity HIGH,CRITICAL --ignore-unfixed --scanners vuln --pkg-types os,library --format table
python scripts/build_residual_risk_report.py \
  --report diagrams=.artifacts/scans/image-security/trivy-diagrams.json \
  --json-output .artifacts/scans/image-security/residual-risk.json \
  --markdown-output .artifacts/scans/image-security/residual-risk.md
```

## Lessons Learned

- release security reporting must encode policy before it can safely gate
- upstream-managed binary findings are common enough that they need first-class classification support
- failing early on scanner output can be less secure when it prevents the repository from publishing the evidence humans need to review

## Applicability

### ✅ This Failure Mode Applies To

- release workflows that scan published images
- images that vendor upstream CLI binaries
- repositories with an explicit upstream residual-risk policy

### ❌ This Failure Mode Does Not Apply To

- repo-owned application dependencies that can be remediated directly in source
- releases with zero findings after scanning
- workflows that do not publish security artifacts

## Status

- [x] Documented
- [x] Prevention implemented
- [x] Detection implemented
- [ ] Mitigation tested
- [ ] Monitoring in place

## Related Knowledge

- `AGENTS.md` release and security policy
- `scripts/build_residual_risk_report.py`
- `.github/workflows/release-images.yml`
