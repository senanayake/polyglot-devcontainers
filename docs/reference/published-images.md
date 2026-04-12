# Published Images

Phase 6 introduces a small published image set rather than publishing every
template immediately.

## Initial images

- `ghcr.io/<owner>/polyglot-devcontainers-maintainer`
- `ghcr.io/<owner>/polyglot-devcontainers-java`
- `ghcr.io/<owner>/polyglot-devcontainers-diagrams`
- `ghcr.io/<owner>/polyglot-devcontainers-python-node`

The maintainer image is published so repository contributors can consume the
same environment that CI validates. It is intentionally broader than the
starter images and is not part of the recommended downstream starter catalog.

## Release note routing

Release notes link each published image to its package page plus the relevant
starter templates and examples.

That mapping is maintained in `published-image-catalog.toml`.

When a published image is added, renamed, or repurposed, update the catalog in
the same change so release notes stay aligned with the repository surface.

## Tag policy

- `sha-<commit>` style immutable tags for every published build
- `main` for the current development line on the default branch
- semantic version tags such as `v0.6.0` for release builds
- `latest` for the newest published semantic-version release

Use a semantic version tag when you need an immutable image reference.

Use `latest` when you want a moving stable release channel and do not want to
edit downstream `devcontainer.json` files for every patch release.

## Validation contract

Each published image must pass `task ci` inside the built container before it
is pushed to the registry.

## Security workflow

Published images are expected to:

- be scanned with Trivy before release
- be signed with Cosign
- have provenance attestations attached

## Registry choice

The default public registry target is GitHub Container Registry (`ghcr.io`).
The images are published as standard OCI images so registry choices can evolve
later without changing the image contract.
