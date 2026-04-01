# Tutorial: Get Podman + DevPod Working on macOS

## Goal

By the end of this tutorial, you will have a working Docker-free development environment using Podman and DevPod on your Mac.

## What You'll Learn

- How to install Podman and DevPod
- How to configure them to work together
- How to create and use development workspaces
- How to verify everything is working correctly

## Time Required

Approximately 15-20 minutes.

## Prerequisites

- macOS computer (Intel or Apple Silicon)
- Administrator access (for optional Docker cleanup)
- Terminal application
- Internet connection

## Step 1: Install Podman

### Download Podman

1. Visit [podman.io](https://podman.io/getting-started/installation)
2. Download the macOS installer (`.pkg` file)
3. Run the installer
4. Follow the installation prompts

The installer will place Podman at `/opt/podman/bin/podman`.

### Verify Installation

Open Terminal and check:

```bash
ls -la /opt/podman/bin/podman
```

You should see the Podman binary listed.

## Step 2: Install DevPod

### Option A: Download from Website

1. Visit [devpod.sh](https://devpod.sh/)
2. Download the macOS version
3. Move DevPod.app to your Applications folder

### Option B: Install with Homebrew

```bash
brew install devpod
```

### Verify Installation

```bash
devpod version
```

You should see the DevPod version number.

## Step 3: Get the Setup Script

### Clone polyglot-devcontainers

```bash
cd ~/dev  # or your preferred directory
git clone https://github.com/senanayake/polyglot-devcontainers.git
cd polyglot-devcontainers
```

The setup script is located at:
```
scripts/setup/setup-podman-devpod-macos.sh
```

## Step 4: Run the Setup Script

### Default Setup (Removes Docker Desktop)

```bash
bash scripts/setup/setup-podman-devpod-macos.sh
```

This will:
- Remove Docker Desktop if present
- Configure your shell
- Initialize Podman machine
- Start Podman service
- Configure DevPod
- Run a test container

### Keep Docker Desktop

If you want to keep Docker alongside Podman:

```bash
bash scripts/setup/setup-podman-devpod-macos.sh --remove-docker-remnants false
```

### Preview Changes (Dry Run)

To see what the script will do without making changes:

```bash
bash scripts/setup/setup-podman-devpod-macos.sh --dry-run
```

## Step 5: Reload Your Shell

After the script completes, reload your shell configuration:

```bash
source ~/.bash_profile
```

Or close and reopen your Terminal.

## Step 6: Verify the Setup

### Check Podman

```bash
which podman
```
Expected output: `/opt/podman/bin/podman`

```bash
podman --version
```
Expected output: `podman version 4.x.x` or higher

```bash
podman info
```
Should display machine and connection information without errors.

### Check DevPod

```bash
devpod provider list
```
Should show `docker` in the list.

```bash
devpod provider options docker
```
Should show `DOCKER_PATH` and `DOCKER_HOST` configured.

### Test Container

```bash
podman run --rm alpine:latest echo "Hello from Podman!"
```
Expected output: `Hello from Podman!`

## Step 7: Create Your First Workspace

### Try a Sample Repository

```bash
devpod up github.com/microsoft/vscode-remote-try-node --ide none
```

This will:
1. Clone the repository
2. Create a container with the devcontainer configuration
3. Set up the development environment

### Connect to the Workspace

```bash
ssh vscode-remote-try-node.devpod
```

You're now inside the container!

### Verify You're in the Container

```bash
pwd
```
Expected: `/workspaces/vscode-remote-try-node`

```bash
ls
```
You should see the repository files.

### Exit the Container

```bash
exit
```

## Step 8: Try a polyglot-devcontainers Template

### Open a Python Template

```bash
cd ~/dev/polyglot-devcontainers
devpod up ./templates/python-secure --ide none
```

### Connect and Initialize

```bash
ssh python-secure.devpod
```

Inside the container:

```bash
task init
```

This bootstraps the Python environment.

### Run the Full Workflow

```bash
task ci
```

This runs:
- `task init` - Bootstrap
- `task lint` - Code quality checks
- `task test` - Run tests
- `task scan` - Security scans

### Exit

```bash
exit
```

## Step 9: Clean Up (Optional)

### List Your Workspaces

```bash
devpod list
```

### Delete a Workspace

```bash
devpod delete vscode-remote-try-node
devpod delete python-secure
```

### Stop Podman

```bash
podman machine stop
```

## Troubleshooting

### "podman: command not found"

Your PATH isn't updated. Run:
```bash
export PATH="/opt/podman/bin:$PATH"
source ~/.bash_profile
```

### "Cannot connect to Podman"

Start the Podman machine:
```bash
podman machine start
```

### DevPod Can't Create Workspace

Restart Podman system service:
```bash
pkill -f "podman system service"
podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
```

### Permission Errors

Ensure Podman machine is running:
```bash
podman machine list
```

## What You've Accomplished

✅ Installed Podman and DevPod  
✅ Configured them to work together  
✅ Created and used development workspaces  
✅ Verified the complete setup  
✅ Tested with polyglot-devcontainers templates  

## Next Steps

### Learn More

- Read `docs/how-to/podman-devpod-macos.md` for detailed operations
- Read `docs/explanation/podman-devpod-macos.md` for architecture details
- Run `man polyglot` inside a container for runtime guidance

### Create Helper Scripts

Create `~/bin/podman-up` and `~/bin/podman-down` for easy management:

**~/bin/podman-up**:
```bash
#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/podman/bin:$PATH"
podman machine start >/dev/null 2>&1 || true
if ! pgrep -f "podman system service --time=0" >/dev/null 2>&1; then
  nohup podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
  sleep 2
fi
echo "Podman ready"
```

**~/bin/podman-down**:
```bash
#!/usr/bin/env bash
set -euo pipefail
export PATH="/opt/podman/bin:$PATH"
pkill -f "podman system service --time=0" >/dev/null 2>&1 || true
podman machine stop >/dev/null 2>&1 || true
echo "Podman stopped"
```

Make them executable:
```bash
chmod +x ~/bin/podman-up ~/bin/podman-down
```

### Explore Templates

Try other polyglot-devcontainers templates:
- `templates/node-secure` - Node/TypeScript environment
- `templates/java-secure` - Java environment
- `templates/python-node-secure` - Polyglot environment

### Use Published Images

Create projects using published images:

```json
{
  "name": "my-project",
  "image": "ghcr.io/senanayake/polyglot-devcontainers-python-node:main",
  "postCreateCommand": "task init"
}
```

## Summary

You now have a Docker-free, reproducible development environment on macOS using Podman and DevPod. This setup:

- Is lightweight and transparent
- Works with existing devcontainer configurations
- Integrates with polyglot-devcontainers templates
- Provides the same workflow as Docker Desktop

Happy coding! 🚀
