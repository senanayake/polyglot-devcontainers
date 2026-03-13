# Container-First Workflow

The Linux container is the source of truth for this repository.

That choice reduces drift across Windows, macOS, and Linux because:

- tool installation happens in a known environment
- CI can mirror local setup more closely
- host package state does not become part of the contract

The host only needs enough capability to open or run the container workflow.
