# Podman + DevPod on macOS: Architecture and Design

## Purpose

This document explains the architecture, design decisions, and technical rationale behind the Podman + DevPod setup for macOS.

## The Container Runtime Problem on macOS

### Why Containers Need Special Handling on macOS

Linux containers rely on kernel features that do not exist in the macOS kernel:

- **Namespaces**: Process, network, mount, user isolation
- **Control Groups (cgroups)**: Resource limiting and accounting
- **Union filesystems**: Efficient layered storage

macOS cannot run Linux containers natively. A Linux environment is required.

### Traditional Solution: Docker Desktop

Docker Desktop provides:
- A Linux VM (using HyperKit or virtualization.framework)
- Docker daemon running inside the VM
- Docker CLI on the host communicating with the daemon
- GUI management interface

**Drawbacks**:
- Heavy resource usage (large VM, always-on daemon)
- Opaque state management
- Proprietary components
- Hidden configuration
- Licensing considerations for commercial use

## The Podman Alternative

### What is Podman?

Podman is a daemonless container engine that:
- Runs containers without a central daemon
- Uses the same OCI (Open Container Initiative) standards as Docker
- Provides Docker-compatible CLI and API
- Supports rootless containers
- Is fully open source (Apache 2.0)

### Podman on macOS: The Machine Concept

On macOS, Podman uses **Podman Machine**:
- A lightweight Linux VM (using QEMU or Apple Virtualization.framework)
- Minimal overhead compared to Docker Desktop
- Explicit lifecycle management
- Transparent configuration

The VM runs:
- Fedora CoreOS (optimized for containers)
- Podman daemon (when API compatibility is needed)
- Container workloads

## Architecture Layers

```
┌─────────────────────────────────────────────────────────┐
│ Developer Tools (VS Code, DevPod, CLI)                  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ DevPod Docker Provider                                   │
│ - DOCKER_PATH=/opt/podman/bin/podman                    │
│ - DOCKER_HOST=unix://<podman-socket>                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Podman System Service (Docker-compatible API)           │
│ - Listens on Unix socket                                │
│ - Translates Docker API calls to Podman operations      │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Podman Machine (Linux VM)                               │
│ - Fedora CoreOS                                         │
│ - Podman runtime                                        │
│ - Container storage                                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│ Containers (OCI-compliant)                              │
└─────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Podman System Service for API Compatibility

**Decision**: Run `podman system service --time=0` in the background.

**Rationale**:
- DevPod's docker provider expects a Docker-compatible API
- Podman can expose this API via a Unix socket
- The `--time=0` flag prevents timeout (service stays running)
- This creates a stable integration point

**Alternative Considered**: Modify DevPod to use Podman CLI directly
- **Rejected**: Would require forking DevPod or waiting for native Podman support
- Current approach is non-invasive and maintainable

### 2. Environment Variable Strategy

**Decision**: Persist `PATH` and `DOCKER_HOST` in `~/.bash_profile`.

**Rationale**:
- Future shells automatically have correct environment
- No manual export commands needed
- `DOCKER_HOST` is computed dynamically from Podman machine state
- Works across terminal sessions and reboots

**Implementation**:
```bash
export PATH="/opt/podman/bin:$PATH"
export DOCKER_HOST="unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')"
```

### 3. Docker Remnant Cleanup

**Decision**: Optionally remove Docker Desktop artifacts by default.

**Rationale**:
- Prevents ambiguity about which runtime is active
- Frees significant disk space (Docker.app VM can be 10+ GB)
- Reduces confusion from stale configurations
- Can be disabled for migration periods

**Cleanup Targets**:
- `/Applications/Docker.app`
- `~/Library/Containers/com.docker.docker`
- `~/Library/Group Containers/group.com.docker`
- `~/.docker`
- System helpers and launch daemons

### 4. Explicit Over Implicit

**Decision**: Make all configuration steps explicit and logged.

**Rationale**:
- Aligns with polyglot-devcontainers' transparency principles
- Users can understand what changed on their system
- Troubleshooting is easier with visible state
- Script can be audited and modified

### 5. Idempotent Operations

**Decision**: Script can be run multiple times safely.

**Rationale**:
- Checks for existing state before modifying
- Appends to profile only if lines are missing
- Skips Podman machine init if already exists
- Safe for iterative development and troubleshooting

## Integration with DevPod

### DevPod Provider Model

DevPod uses a **provider** abstraction:
- Providers define how to create and manage workspaces
- Built-in providers: docker, kubernetes, ssh, local
- Each provider has configurable options

### Docker Provider Configuration

The docker provider expects:
- `DOCKER_PATH`: Path to docker binary
- `DOCKER_HOST`: Docker daemon socket

**Our Configuration**:
```bash
DOCKER_PATH=/opt/podman/bin/podman
DOCKER_HOST=unix://<podman-socket-path>
```

**Why This Works**:
- Podman CLI is Docker-compatible (same commands, flags)
- Podman system service provides Docker-compatible API
- DevPod cannot distinguish between Docker and Podman

### Workspace Lifecycle

1. **Create**: `devpod up <source>`
   - DevPod calls Podman to create container
   - Mounts workspace directory
   - Runs devcontainer lifecycle commands

2. **Connect**: `ssh <workspace>.devpod`
   - DevPod manages SSH keys and configuration
   - Connects to container via SSH

3. **Delete**: `devpod delete <workspace>`
   - DevPod calls Podman to remove container
   - Cleans up workspace state

## Comparison with Docker Desktop

| Aspect | Docker Desktop | Podman + DevPod |
|--------|----------------|-----------------|
| **VM Size** | Large (10+ GB) | Minimal (2-3 GB) |
| **Daemon** | Always running | On-demand service |
| **State** | Opaque | Transparent |
| **Configuration** | GUI + hidden files | Explicit scripts |
| **Resource Usage** | High baseline | Lower baseline |
| **CLI** | Docker-specific | Docker-compatible |
| **API** | Docker API | Docker-compatible API |
| **License** | Proprietary terms | Apache 2.0 |
| **Updates** | Automatic (sometimes disruptive) | Manual (controlled) |

## Security Considerations

### Rootless Containers

Podman supports rootless containers:
- Containers run as non-root user
- Reduced attack surface
- Better multi-user isolation

**Note**: Podman Machine on macOS runs the VM as the user, providing similar isolation to Docker Desktop.

### Socket Permissions

The Podman socket is user-scoped:
- Located in user's runtime directory
- Not accessible to other users
- No privileged daemon required

### Secrets Management

Both Docker and Podman:
- Should not store secrets in images
- Support secret mounting at runtime
- Integrate with external secret managers

**Best Practice**: Use environment variables or mounted secret files, never hardcode.

## Performance Characteristics

### Startup Time

- **Podman Machine**: ~5-10 seconds
- **Docker Desktop**: ~10-20 seconds

### Container Operations

- **Create/Start**: Similar performance
- **Build**: Similar performance (both use BuildKit or compatible)
- **Network**: Similar performance (both use VM networking)

### Resource Efficiency

Podman advantages:
- No always-on daemon overhead
- Smaller VM footprint
- More explicit resource allocation

## Troubleshooting Architecture

### Common Failure Points

1. **Podman Machine Not Running**
   - Symptom: "Cannot connect to Podman"
   - Fix: `podman machine start`

2. **System Service Not Running**
   - Symptom: DevPod cannot create workspaces
   - Fix: Restart `podman system service`

3. **Socket Path Mismatch**
   - Symptom: DOCKER_HOST points to wrong location
   - Fix: Re-run socket path detection

4. **PATH Not Updated**
   - Symptom: `podman: command not found`
   - Fix: Source profile or add to PATH manually

### Diagnostic Commands

```bash
# Check Podman availability
which podman
podman --version

# Check machine status
podman machine list
podman machine inspect

# Check service status
pgrep -f "podman system service"

# Check socket
echo $DOCKER_HOST
ls -la $(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')

# Check DevPod configuration
devpod provider list
devpod provider options docker
```

## Future Considerations

### Apple Silicon Optimization

Apple Silicon Macs can use:
- Native virtualization.framework (faster than QEMU)
- ARM64 container images (better performance)

The setup script works on both Intel and Apple Silicon.

### Rootless Mode Improvements

Future Podman versions may:
- Improve rootless networking
- Reduce permission requirements
- Enhance multi-user scenarios

### DevPod Native Podman Support

If DevPod adds native Podman provider:
- Could eliminate system service requirement
- Might provide better integration
- Current approach remains valid fallback

## Alignment with polyglot-devcontainers Principles

### Container-First Workflow

✅ Aligns with project's container-first philosophy
- Development happens inside containers
- Host provides only runtime and tooling
- Reproducible across machines

### Explicit Configuration

✅ Follows transparency principles
- All setup steps are documented and scripted
- No hidden state or magic configuration
- Users understand what changed

### Executable Knowledge

✅ Embodies Phase 10 goals
- Setup is a runnable scenario
- Can be verified and validated
- Produces observable artifacts
- Teaches through execution

### Security-First

✅ Maintains security posture
- Explicit permission model
- User-scoped resources
- No unnecessary privileges
- Auditable configuration

## Conclusion

The Podman + DevPod architecture provides:

1. **Docker Desktop Alternative**: Full functionality without proprietary components
2. **Transparent Operation**: Explicit configuration and state management
3. **Lightweight Runtime**: Minimal resource overhead
4. **Developer-Friendly**: Compatible with existing Docker workflows
5. **Reproducible**: Scripted setup that can be version-controlled

This approach demonstrates how executable knowledge systems can solve real infrastructure problems while maintaining clarity, security, and reproducibility.

## References

- [Podman Documentation](https://docs.podman.io/)
- [Podman Machine Architecture](https://docs.podman.io/en/latest/markdown/podman-machine.1.html)
- [DevPod Provider Documentation](https://devpod.sh/docs/developing-providers/provider-spec)
- [OCI Specifications](https://opencontainers.org/)
- [Dev Container Specification](https://containers.dev/)
