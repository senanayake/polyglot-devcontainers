# How to Set Up Podman + DevPod on macOS

## Overview

This guide shows you how to configure a Docker-free development environment on macOS using Podman and DevPod.

## Prerequisites

- macOS (Intel or Apple Silicon)
- Podman CLI installed (download from [podman.io](https://podman.io/getting-started/installation))
- DevPod installed (download from [devpod.sh](https://devpod.sh/))
- Bash shell

## Installation Steps

### 1. Install Podman

Download and install Podman Desktop or CLI from the official installer. The default installation places the binary at:

```
/opt/podman/bin/podman
```

### 2. Install DevPod

Download DevPod from the official website or use Homebrew:

```bash
brew install devpod
```

### 3. Run the Setup Script

From the polyglot-devcontainers repository:

```bash
bash scripts/setup/setup-podman-devpod-macos.sh
```

The script will:
- Configure your shell environment
- Initialize Podman machine
- Start Podman system service
- Configure DevPod to use Podman
- Validate the setup

### 4. Reload Your Shell

```bash
source ~/.bash_profile
```

## Verification

### Check Podman

```bash
which podman
# Expected: /opt/podman/bin/podman

podman --version
# Expected: podman version 4.x.x or higher

podman info
# Should show machine and connection details
```

### Check DevPod Configuration

```bash
devpod provider list
# Should show 'docker' provider

devpod provider options docker
# Should show DOCKER_PATH and DOCKER_HOST configured
```

### Test Container Runtime

```bash
podman run --rm alpine:latest echo "Hello from Podman"
```

## Common Tasks

### Start Your Environment

Create helper scripts for convenience:

**~/bin/podman-up**:
```bash
#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/podman/bin:$PATH"

echo "Starting Podman machine..."
podman machine start >/dev/null 2>&1 || true

echo "Starting Podman service..."
if ! pgrep -f "podman system service --time=0" >/dev/null 2>&1; then
  nohup podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
  sleep 2
fi

export DOCKER_HOST="unix://$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')"

echo "Podman ready"
echo "DOCKER_HOST=$DOCKER_HOST"
```

**~/bin/podman-down**:
```bash
#!/usr/bin/env bash
set -euo pipefail

export PATH="/opt/podman/bin:$PATH"

echo "Stopping Podman service..."
pkill -f "podman system service --time=0" >/dev/null 2>&1 || true

echo "Stopping Podman machine..."
podman machine stop >/dev/null 2>&1 || true

echo "Podman stopped"
```

Make them executable:
```bash
chmod +x ~/bin/podman-up ~/bin/podman-down
```

### Create a DevPod Workspace

```bash
# From a GitHub repository
devpod up github.com/microsoft/vscode-remote-try-node --ide none

# From a local directory
devpod up /path/to/your/project --ide none

# SSH into the workspace
ssh <workspace-name>.devpod
```

### List Workspaces

```bash
devpod list
```

### Delete a Workspace

```bash
devpod delete <workspace-name>
```

### Clean Up Disk Space

```bash
# Check disk usage
podman system df

# Prune unused containers, images, volumes
podman system prune -a -f
```

## Using with polyglot-devcontainers

### Open a Template

```bash
# Clone the repository
git clone https://github.com/senanayake/polyglot-devcontainers.git
cd polyglot-devcontainers

# Use DevPod to open a template
devpod up ./templates/python-secure --ide none
ssh python-secure.devpod

# Inside the container
task init
task ci
```

### Use Published Images

```bash
# Create a devcontainer.json pointing to a published image
{
  "name": "my-python-project",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:main",
  "postCreateCommand": "task init"
}

# Open with DevPod
devpod up . --ide none
```

## Troubleshooting

### Podman Machine Won't Start

```bash
# Check machine status
podman machine list

# Stop and restart
podman machine stop
podman machine start

# If corrupted, reinitialize
podman machine rm
podman machine init
podman machine start
```

### DevPod Cannot Connect to Podman

```bash
# Verify socket path
podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}'

# Ensure DOCKER_HOST is set
echo $DOCKER_HOST

# Restart Podman service
pkill -f "podman system service"
podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
```

### Permission Denied Errors

```bash
# Ensure Podman machine is running as your user
podman machine list

# Check socket permissions
ls -la $(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')
```

### Service Logs

Check Podman service logs:
```bash
tail -f /tmp/podman-system-service.log
```

## Advanced Configuration

### Custom Podman Machine Settings

```bash
# Initialize with more resources
podman machine init --cpus 4 --memory 8192 --disk-size 100
```

### Multiple Podman Machines

```bash
# Create a named machine
podman machine init my-dev-machine

# Start specific machine
podman machine start my-dev-machine

# Set as default
podman system connection default my-dev-machine
```

### DevPod IDE Integration

```bash
# Open with VS Code
devpod up <workspace> --ide vscode

# Open with JetBrains IDE
devpod up <workspace> --ide intellij
```

## Migration from Docker Desktop

If you're migrating from Docker Desktop:

1. **Export existing images** (optional):
   ```bash
   docker save -o myimage.tar myimage:tag
   podman load -i myimage.tar
   ```

2. **Run the setup script** with Docker cleanup:
   ```bash
   bash scripts/setup/setup-podman-devpod-macos.sh --remove-docker-remnants true
   ```

3. **Update scripts** that reference `docker` to use `podman` or rely on the alias

4. **Test your workflows** to ensure compatibility

## Best Practices

1. **Start Podman on login**: Add `podman-up` to your shell profile
2. **Monitor resources**: Use `podman stats` to watch container resource usage
3. **Regular cleanup**: Run `podman system prune` weekly
4. **Version control**: Keep your devcontainer.json in Git
5. **Use published images**: Prefer stable images over local builds

## See Also

- [Podman Documentation](https://docs.podman.io/)
- [DevPod Documentation](https://devpod.sh/docs)
- `man polyglot-starters` - Starter templates
- `man polyglot-task-contract` - Task workflow
- `docs/explanation/podman-devpod-macos.md` - Architecture details
