# Release Images

This repository publishes images through GitHub Actions.

## Trigger the release workflow

The release workflow is defined in `.github/workflows/release-images.yml`.

It can run:

- manually with workflow dispatch
- on pushes to `main`
- on semantic version tags such as `v0.6.0`

## What the workflow does

For each published image, the workflow:

1. builds the image
2. runs `task ci` inside the built image
3. scans the image with Trivy
4. pushes the image to GHCR
5. signs the image with Cosign
6. attaches build provenance

## Initial published image set

- the root repository image built from `.devcontainer/Containerfile`
- the Python plus Node / TypeScript image built from `templates/python-node-secure/.devcontainer/Containerfile`

## Verify the registry target

The workflow publishes to `ghcr.io/${owner}/...` using the repository
`GITHUB_TOKEN`.

To keep package linkage working correctly, the Containerfiles include the
`org.opencontainers.image.source` OCI label.
