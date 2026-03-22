# Release Images

This repository publishes images through GitHub Actions.

Published image maintenance is a separate preparation step from the release
workflow itself.

These maintenance tasks are intended to run from the maintainer container, not
from the host shell.

The default maintainer execution path is:

```bash
task maintainer:pull
task maintainer:task -- ci
```

The host should only pull and start the maintainer container. Repository
workflow proof still has to happen inside that container.

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

## Initial published image set

- the root repository image built from `.devcontainer/Containerfile`
- the Gradle-first Java image built from `templates/java-secure/.devcontainer/Containerfile`
- the Python plus Node / TypeScript image built from `templates/python-node-secure/.devcontainer/Containerfile`

## Verify the registry target

The workflow publishes to `ghcr.io/${owner}/...` using the repository
`GITHUB_TOKEN`.

To keep package linkage working correctly, the Containerfiles include the
`org.opencontainers.image.source` OCI label.
