# Published Images

Phase 6 introduces a small published image set rather than publishing every
template immediately.

## Initial images

- `ghcr.io/<owner>/polyglot-devcontainers-root`
- `ghcr.io/<owner>/polyglot-devcontainers-python-node`

## Tag policy

- `sha-<commit>` style immutable tags for every published build
- `main` for the current development line on the default branch
- semantic version tags such as `v0.6.0` for release builds

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
