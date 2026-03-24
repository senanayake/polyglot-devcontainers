# Release Images

This repository publishes images through GitHub Actions.

Published image maintenance is a separate preparation step from the release
workflow itself.

These maintenance tasks are intended to run from the maintainer container, not
from the host shell.

The default maintainer execution path is:

```bash
task maintainer:up
task maintainer:task -- ci
task maintainer:git -- status --short --branch
```

The host should only control the maintainer devcontainer through the official
Dev Containers CLI entrypoint used by the repository wrapper. Repository
workflow proof still has to happen inside that container.

For HTTPS remotes, use `task maintainer:git -- ...` for the release commit and
push path as well. The wrapper can inject credentials into a single
container-side Git command without persisting them in the container.

## Maintain the maintainer container

The dedicated maintainer workflow is defined in
`.github/workflows/maintainer-image.yml`.

It publishes the maintainer image on `main` so agents can pull a fresh GHCR
artifact instead of rebuilding the maintainer image on the host.

## Trigger the release workflow

The release workflow is defined in `.github/workflows/release-images.yml`.

It can run:

- manually with workflow dispatch
- on semantic version tags such as `v0.6.0`

## What the workflow does

For each published image, the workflow:

1. builds the image
2. runs `task ci` inside the built image
3. scans the image with Trivy
4. pushes the image to GHCR
5. signs the image with Cosign
6. attaches build provenance
7. uploads release security assets and adds a `Security Status` section to the GitHub Release

## Find release security status

After a tag-triggered release succeeds, open the GitHub Release page for that
tag.

The release notes now include a generated `Security Status` section with:

- per-image Critical / High / Total counts
- direct links to the per-image summary Markdown and JSON assets
- direct links to the per-image SBOM assets
- a release-level residual-risk report for critical findings that remain in the
  latest upstream-supported third-party binaries

The release also publishes these assets directly:

- `release-security-overview.md`
- `release-security-<image>-summary.md`
- `release-security-<image>-summary.json`
- `release-security-<image>-sbom.spdx.json`
- `release-security-residual-risk.md`
- `release-security-residual-risk.json`

## Maintain published image bases

Use the repository tasks to refresh the published image base references before
cutting a release:

```bash
task image:discover
task image:pin -- --write
task image:verify
task image:scan
```

The initial scope is only the published images:

- `.devcontainer/Containerfile`
- `templates/java-secure/.devcontainer/Containerfile`
- `templates/python-node-secure/.devcontainer/Containerfile`

`task image:pin` is report-only unless you pass `--write`.

The discovery and scan steps write evidence under:

- `.artifacts/scans/base-image-report.json`
- `.artifacts/scans/base-image-report.md`
- `.artifacts/scans/image-security/`
- `.artifacts/scans/image-security/residual-risk.json`
- `.artifacts/scans/image-security/residual-risk.md`

## Classify remaining findings

When published-image scans still report critical findings after a refresh,
agents should classify them in this order:

1. `repo-fixable`
2. `upstream residual`

`repo-fixable` findings include:

- stale published-image base digests
- stale distro packages that clear with a rebuild and security upgrade
- stale pinned tool versions in repository-owned install logic
- missing verification for downloaded archives or signing keys

`upstream residual` findings are findings that remain in the latest
upstream-supported binary release for third-party tools such as `trivy`,
`gitleaks`, or `task`.

For upstream residual findings:

- keep the upstream release artifact
- record the finding in the residual-risk report
- wait for a new upstream release

Agents should not privately rebuild or patch those third-party tools only to
silence scanner output unless a human explicitly asks for that exception.

## Initial published image set

- the root repository image built from `.devcontainer/Containerfile`
- the Gradle-first Java image built from `templates/java-secure/.devcontainer/Containerfile`
- the Python plus Node / TypeScript image built from `templates/python-node-secure/.devcontainer/Containerfile`

## Verify the registry target

The workflow publishes to `ghcr.io/${owner}/...` using the repository
`GITHUB_TOKEN`.

To keep package linkage working correctly, the Containerfiles include the
`org.opencontainers.image.source` OCI label.
