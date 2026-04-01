# Podman + DevPod on macOS Scenario

## Purpose

This scenario demonstrates how to set up a Docker-free, reproducible development environment on macOS using Podman and DevPod.

## Target Audience

- macOS users (Intel or Apple Silicon)
- Developers wanting to migrate from Docker Desktop
- Users seeking a lightweight, transparent container runtime
- Teams requiring reproducible development environments

## What This Scenario Covers

1. Installing and configuring Podman on macOS
2. Setting up Podman machine (the Linux VM required on macOS)
3. Configuring Podman system service for Docker-compatible API
4. Integrating DevPod to use Podman instead of Docker
5. Validating the complete setup

## Prerequisites

Before running this scenario:

- macOS system (tested on Intel Macs)
- Podman CLI installed at `/opt/podman/bin/podman`
- DevPod installed and available on PATH
- Bash shell (default on macOS)
- Optional: Docker Desktop if you want automatic cleanup

## Running the Scenario

### Quick Start

```bash
# From the repository root
bash scripts/setup/setup-podman-devpod-macos.sh
```

### Dry Run (Preview Actions)

```bash
bash scripts/setup/setup-podman-devpod-macos.sh --dry-run
```

### Keep Docker Desktop

```bash
bash scripts/setup/setup-podman-devpod-macos.sh --remove-docker-remnants false
```

## What the Script Does

1. **Optional Docker Cleanup**: Removes Docker Desktop remnants to avoid conflicts
2. **PATH Configuration**: Adds Podman to your shell PATH
3. **Environment Setup**: Configures `DOCKER_HOST` for Podman socket
4. **Podman Machine**: Initializes and starts the Podman VM
5. **System Service**: Starts Podman's Docker-compatible API service
6. **DevPod Integration**: Configures DevPod to use Podman
7. **Validation**: Runs a test container to verify the setup

## Post-Setup Verification

After running the script:

```bash
# Reload your shell environment
source ~/.bash_profile

# Verify Podman
which podman
podman info

# Verify DevPod configuration
devpod provider list
devpod provider options docker

# Test a DevPod workspace
devpod up github.com/microsoft/vscode-remote-try-node --ide none
ssh vscode-remote-try-node.devpod
```

## Architecture

```
DevPod → Docker Provider → Podman Socket → Podman Machine (VM) → Containers
```

### Key Components

- **Podman Machine**: Lightweight Linux VM for running containers on macOS
- **Podman System Service**: Docker-compatible API exposed via Unix socket
- **DevPod Docker Provider**: Configured to use Podman binary and socket
- **Shell Configuration**: Persistent PATH and DOCKER_HOST settings

## Why This Approach Works

1. **Docker Desktop Independence**: No heavy VM or proprietary tooling
2. **Transparent State**: All configuration is explicit and inspectable
3. **Reproducible**: Script can be version-controlled and shared
4. **Compatible**: Works with tools expecting Docker API
5. **Lightweight**: Podman machine is more resource-efficient

## Common Operations

### Start Podman Environment

```bash
podman machine start
podman system service --time=0 &
```

### Stop Podman Environment

```bash
pkill -f "podman system service"
podman machine stop
```

### Check Podman Status

```bash
podman machine list
podman info
```

### Clean Up Disk Space

```bash
podman system df
podman system prune -a -f
```

## Troubleshooting

### Podman Not Found

Ensure `/opt/podman/bin` is in your PATH:
```bash
export PATH="/opt/podman/bin:$PATH"
```

### DevPod Cannot Connect

Check Podman socket:
```bash
podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}'
```

### Service Not Running

Restart Podman system service:
```bash
pkill -f "podman system service"
podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
```

## Integration with polyglot-devcontainers

This scenario demonstrates:

- **Executable Knowledge**: Setup is scripted and verifiable
- **Reproducible Environments**: Configuration is explicit and portable
- **Container-First Workflow**: Aligns with project's devcontainer approach
- **Documentation as Code**: Script itself is heavily documented

## Next Steps

After completing this scenario:

1. Use DevPod to open polyglot-devcontainers templates
2. Test Python, Node, or Java starter environments
3. Verify `task ci` works inside Podman-backed containers
4. Extend this approach to other macOS configurations (Apple Silicon)

## Related Documentation

- `man polyglot-starters` - Starter template guidance
- `man polyglot-task-contract` - Task workflow reference
- `docs/how-to/podman-devpod-macos.md` - Detailed how-to guide
- `docs/explanation/podman-devpod-macos.md` - Architecture explanation
