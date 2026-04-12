---
id: KB-2026-011
type: operational
status: active
created: 2026-04-12
updated: 2026-04-12
tags: [vscode, podman, windows, devcontainers, host-runtime, consumer-setup]
related: [KB-2026-010]
---

# VS Code Dev Containers with Podman on Windows: Host Runtime Binding

## Context

A downstream consumer workspace was opened on a Windows machine that should use
Podman rather than Docker for Dev Containers.

The machine already had Podman installed and a working machine connection, but
VS Code still prompted:

> Dev Containers require docker to run. Do you want to install Docker in WSL?

## Problem

The host editor was configured with a Linux Docker path:

```json
"dev.containers.dockerPath": "/usr/bin/docker"
```

That setting is invalid for a Windows-hosted VS Code session using Podman.

As a result, the editor framed the problem as "missing Docker in WSL" instead
of using the local Windows Podman client.

## Evidence

### Host Settings Mismatch

The relevant setting was:

```json
"dev.containers.dockerPath": "/usr/bin/docker"
```

This path only makes sense inside a Linux environment. It is not the correct
control path for a Windows host editor.

### Podman Itself Was Reachable

Once the machine finished starting, the following worked on the host:

```powershell
podman info --debug
```

That confirmed the runtime was available and the problem was editor/runtime
binding, not Podman installation.

### Non-Blocking Warning

`podman machine start` emitted:

```text
API forwarding for Docker API clients is not available ...
CreateFile \\.\pipe\docker_engine: All pipe instances are busy.
Podman clients are still able to connect.
```

This warning is not the same as Podman being unavailable. It only means the
Docker-compatible forwarding pipe is not ready.

## Decision

For Windows-hosted VS Code using Podman machines, `dev.containers.dockerPath`
must point to the Windows Podman executable, not to a Linux Docker path.

Recommended setting:

```json
"dev.containers.dockerPath": "C:\\Users\\chris\\AppData\\Local\\Programs\\Podman\\podman.exe"
```

`"podman"` is acceptable when the executable is reliably on `PATH`, but the
full path is less ambiguous.

## Operational Guidance

Use this startup sequence:

```powershell
podman machine start
podman info
```

Treat `podman info` success as the readiness gate. Do not assume that the
message "already running" means the API forwarding path is ready.

## Implications

- VS Code Dev Containers can work on this machine without Docker Desktop.
- The user should not be instructed to install Docker in WSL when Podman is
  the intended runtime.
- Documentation for downstream Windows consumers should explicitly cover this
  host setting.
