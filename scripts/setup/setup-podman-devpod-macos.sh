#!/usr/bin/env bash
#
# setup-podman-devpod-macos.sh
#
# Purpose
# -------
# This script installs and wires together a Docker-free local container workflow
# on macOS using:
#
#   1. Podman CLI
#   2. Podman machine (the lightweight Linux VM Podman uses on macOS)
#   3. Podman system service (Docker-compatible socket/API)
#   4. DevPod using its built-in "docker" provider, pointed at Podman
#
# It can also optionally remove Docker Desktop remnants first.
#
# Why this script exists
# ----------------------
# On macOS, container runtimes do not run natively in the same way they do on Linux.
# Podman therefore uses a small VM ("podman machine") to run Linux containers.
#
# DevPod commonly expects a Docker-style provider interface. Podman can satisfy
# that expectation by exposing a Docker-compatible socket and CLI behavior.
#
# This script makes that wiring explicit and repeatable.
#
# High-level workflow
# -------------------
# 1. Optionally remove Docker Desktop remnants
# 2. Ensure Podman is on PATH
# 3. Persist PATH and environment configuration for future bash shells
# 4. Initialize/start Podman machine
# 5. Start Podman system service (Docker-compatible API)
# 6. Point DevPod's built-in docker provider at Podman
# 7. Verify the setup with a simple test container
#
# Usage
# -----
# Default behavior:
#   ./setup-podman-devpod-macos.sh
#
# Disable Docker-remnant cleanup:
#   ./setup-podman-devpod-macos.sh --remove-docker-remnants false
#
# Dry-run mode (show what would happen without executing destructive commands):
#   ./setup-podman-devpod-macos.sh --dry-run
#
# Assumptions
# -----------
# - You already installed Podman CLI using the official installer and the binary is at:
#       /opt/podman/bin/podman
# - You already installed DevPod and it is available on PATH somewhere
# - You use bash and want persistence in ~/.bash_profile
#
# Notes
# -----
# - This script is intentionally verbose and heavily documented.
# - It is written to be understandable and maintainable, not merely short.
# - It avoids silently doing risky things.
#

set -euo pipefail

########################################
# Configuration defaults
########################################

# The official Podman CLI installer often places the binary here on macOS.
PODMAN_BIN_DEFAULT="/opt/podman/bin/podman"

# Bash startup file used to persist PATH and environment variables.
BASH_PROFILE_DEFAULT="${HOME}/.bash_profile"

# By default, remove Docker remnants. This is what you asked for.
REMOVE_DOCKER_REMNANTS="true"

# Dry-run mode prints actions instead of executing them.
DRY_RUN="false"

########################################
# Mutable runtime variables
########################################

PODMAN_BIN="$PODMAN_BIN_DEFAULT"
BASH_PROFILE="$BASH_PROFILE_DEFAULT"

########################################
# Logging helpers
########################################

timestamp() {
  date '+%Y-%m-%d %H:%M:%S'
}

log() {
  printf '\n[%s] %s\n' "$(timestamp)" "$*"
}

warn() {
  printf '\n[%s] WARNING: %s\n' "$(timestamp)" "$*" >&2
}

fail() {
  printf '\n[%s] ERROR: %s\n' "$(timestamp)" "$*" >&2
  exit 1
}

########################################
# Command execution helper
#
# Why this exists:
# - Centralizes dry-run behavior
# - Makes logs consistent
# - Helps keep dangerous operations visible
########################################

run() {
  if [[ "$DRY_RUN" == "true" ]]; then
    printf '[DRY-RUN] %s\n' "$*"
  else
    eval "$@"
  fi
}

########################################
# Usage text
########################################

usage() {
  cat <<EOF
Usage:
  $0 [options]

Options:
  --remove-docker-remnants true|false
      Whether to remove Docker Desktop remnants before configuring Podman + DevPod.
      Default: true

  --podman-bin /path/to/podman
      Override Podman binary location.
      Default: /opt/podman/bin/podman

  --bash-profile /path/to/profile
      Override bash profile path.
      Default: ~/.bash_profile

  --dry-run
      Print actions without executing them.

  --help
      Show this help text.

Examples:
  $0
  $0 --remove-docker-remnants false
  $0 --dry-run
EOF
}

########################################
# Argument parsing
########################################

while [[ $# -gt 0 ]]; do
  case "$1" in
    --remove-docker-remnants)
      [[ $# -ge 2 ]] || fail "Missing value for --remove-docker-remnants"
      REMOVE_DOCKER_REMNANTS="$2"
      shift 2
      ;;
    --podman-bin)
      [[ $# -ge 2 ]] || fail "Missing value for --podman-bin"
      PODMAN_BIN="$2"
      shift 2
      ;;
    --bash-profile)
      [[ $# -ge 2 ]] || fail "Missing value for --bash-profile"
      BASH_PROFILE="$2"
      shift 2
      ;;
    --dry-run)
      DRY_RUN="true"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      fail "Unknown argument: $1"
      ;;
  esac
done

case "$REMOVE_DOCKER_REMNANTS" in
  true|false) ;;
  *) fail "--remove-docker-remnants must be true or false" ;;
esac

########################################
# Utility functions
########################################

require_cmd() {
  command -v "$1" >/dev/null 2>&1 || fail "Required command not found on PATH: $1"
}

require_file_executable() {
  local path="$1"
  [[ -x "$path" ]] || fail "Expected executable not found: $path"
}

append_if_missing() {
  local line="$1"
  local file="$2"

  if [[ ! -f "$file" ]]; then
    run "touch \"$file\""
  fi

  if grep -Fqx "$line" "$file" 2>/dev/null; then
    log "Line already present in $file: $line"
  else
    log "Appending line to $file: $line"
    if [[ "$DRY_RUN" == "true" ]]; then
      printf '[DRY-RUN] echo %q >> %q\n' "$line" "$file"
    else
      printf '%s\n' "$line" >> "$file"
    fi
  fi
}

########################################
# Docker cleanup
#
# Why this exists:
# - Docker Desktop on macOS stores a large VM disk image and app data
#   in user Library locations and system helper locations.
# - Leaving Docker remnants around can waste disk space and can also
#   create ambiguity about which runtime/tools are active.
# - This cleanup is optional because some users may want to keep Docker
#   installed alongside Podman during a migration period.
########################################

remove_docker_remnants() {
  log "Docker remnant cleanup enabled."

  # Stop Docker Desktop process if it is still running.
  # Why:
  # - Prevents file locks
  # - Avoids race conditions while removing Docker app data
  run "killall Docker 2>/dev/null || true"

  # Remove the Docker Desktop application bundle.
  # Why:
  # - Prevents accidental reuse
  # - Removes the GUI app itself
  if [[ -d "/Applications/Docker.app" ]]; then
    log "Removing Docker.app"
    run "rm -rf \"/Applications/Docker.app\""
  else
    log "Docker.app not present; skipping."
  fi

  # Remove primary Docker Desktop user container storage.
  # Why:
  # - This is typically where the big Docker VM disk lived
  # - Often the main source of disk bloat
  if [[ -d "${HOME}/Library/Containers/com.docker.docker" ]]; then
    log "Removing ~/Library/Containers/com.docker.docker"
    run "rm -rf \"${HOME}/Library/Containers/com.docker.docker\""
  else
    log "Docker user container storage not present; skipping."
  fi

  # Remove Docker shared group container data.
  # Why:
  # - Docker Desktop also stores shared app/group state here
  if [[ -d "${HOME}/Library/Group Containers/group.com.docker" ]]; then
    log "Removing ~/Library/Group Containers/group.com.docker"
    run "rm -rf \"${HOME}/Library/Group Containers/group.com.docker\""
  else
    log "Docker group container data not present; skipping."
  fi

  # Remove per-user Docker CLI/config metadata.
  # Why:
  # - Clears old contexts, auth info, config, and state
  # - Helps make the new Podman-based setup unambiguous
  if [[ -d "${HOME}/.docker" ]]; then
    log "Removing ~/.docker"
    run "rm -rf \"${HOME}/.docker\""
  else
    log "~/.docker not present; skipping."
  fi

  # Remove Docker privileged helpers if present.
  # Why:
  # - Docker Desktop may install helper tools and launch daemons
  # - Removing them reduces leftover system-level artifacts
  if [[ -e "/Library/PrivilegedHelperTools/com.docker.vmnetd" ]]; then
    log "Removing /Library/PrivilegedHelperTools/com.docker.vmnetd"
    run "sudo rm -f \"/Library/PrivilegedHelperTools/com.docker.vmnetd\""
  else
    log "Docker privileged helper not present; skipping."
  fi

  if [[ -e "/Library/LaunchDaemons/com.docker.vmnetd.plist" ]]; then
    log "Removing /Library/LaunchDaemons/com.docker.vmnetd.plist"
    run "sudo rm -f \"/Library/LaunchDaemons/com.docker.vmnetd.plist\""
  else
    log "Docker launch daemon plist not present; skipping."
  fi

  # Optional cleanup of docker shims in /usr/local/bin.
  # Why:
  # - If these remain, tools or users may accidentally call stale Docker binaries
  # - We do not fail if they are absent
  if [[ -e "/usr/local/bin/docker" ]]; then
    log "Removing /usr/local/bin/docker"
    run "sudo rm -f \"/usr/local/bin/docker\""
  else
    log "/usr/local/bin/docker not present; skipping."
  fi

  if [[ -e "/usr/local/bin/docker-compose" ]]; then
    log "Removing /usr/local/bin/docker-compose"
    run "sudo rm -f \"/usr/local/bin/docker-compose\""
  else
    log "/usr/local/bin/docker-compose not present; skipping."
  fi

  log "Docker remnant cleanup complete."
}

########################################
# Environment setup
#
# Why this exists:
# - The official Podman installer may not modify PATH automatically
# - Future shells need to find podman without manual export commands
# - DevPod's docker provider needs a stable DOCKER_HOST value
########################################

configure_bash_profile() {
  log "Persisting environment settings in ${BASH_PROFILE}"

  append_if_missing 'export PATH="/opt/podman/bin:$PATH"' "$BASH_PROFILE"

  # This line computes the Podman socket path dynamically each time a bash shell starts.
  # Why:
  # - The socket path is derived from Podman machine state
  # - This avoids hardcoding a path that could differ between systems
  append_if_missing 'export DOCKER_HOST="unix://$(podman machine inspect --format '\''{{.ConnectionInfo.PodmanSocket.Path}}'\'' 2>/dev/null || true)"' "$BASH_PROFILE"

  # This alias is optional, but useful in migration periods.
  # Why:
  # - Many developer habits and scripts still type "docker"
  # - This lets interactive bash sessions treat docker as podman
  # - It does not affect DevPod provider config directly; that is configured separately
  append_if_missing 'alias docker=podman' "$BASH_PROFILE"
}

########################################
# Podman initialization
#
# Why this exists:
# - On macOS, Podman needs a Linux VM ("podman machine")
# - The machine must exist and be started before container workloads run
########################################

initialize_and_start_podman_machine() {
  export PATH="/opt/podman/bin:$PATH"
  hash -r

  command -v podman >/dev/null 2>&1 || fail "podman not found even after updating PATH"
  log "Using podman at: $(command -v podman)"
  log "Podman version: $(podman --version)"

  # Determine whether a machine already exists.
  # Why:
  # - podman machine init should only run once per machine unless reinitializing
  if podman machine inspect >/dev/null 2>&1; then
    log "Podman machine already exists; skipping init."
  else
    log "Initializing Podman machine"
    run "podman machine init"
  fi

  # Start the machine.
  # Why:
  # - The Podman VM must be active before Podman can run containers on macOS
  log "Starting Podman machine"
  run "podman machine start || true"

  # Basic verification.
  # Why:
  # - Fails early if machine startup did not work
  log "Verifying Podman machine with podman info"
  run "podman info >/dev/null"
}

########################################
# Podman API service
#
# Why this exists:
# - DevPod's built-in docker provider expects Docker-like semantics
# - Podman can provide a Docker-compatible API/socket via "podman system service"
# - The --time=0 flag keeps the service from timing out
########################################

start_podman_system_service() {
  export PATH="/opt/podman/bin:$PATH"
  hash -r

  local socket_path
  socket_path="$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')"
  export DOCKER_HOST="unix://${socket_path}"

  log "Podman socket path resolved to: ${DOCKER_HOST}"

  # Start background system service if not already running.
  # Why:
  # - Prevent duplicate background services
  # - Avoids noise and potential confusion
  if pgrep -f "podman system service --time=0" >/dev/null 2>&1; then
    log "Podman system service already running."
  else
    log "Starting Podman system service in background"
    if [[ "$DRY_RUN" == "true" ]]; then
      printf '[DRY-RUN] nohup podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &\n'
    else
      nohup podman system service --time=0 >/tmp/podman-system-service.log 2>&1 &
      sleep 2
    fi
  fi
}

########################################
# DevPod configuration
#
# Why this exists:
# - DevPod has a built-in "docker" provider
# - We want that provider to call Podman instead of Docker
# - This is done by setting:
#     DOCKER_PATH -> Podman binary
#     DOCKER_HOST -> Podman socket
########################################

configure_devpod_for_podman() {
  export PATH="/opt/podman/bin:$PATH"
  hash -r

  require_cmd devpod

  local socket_path
  socket_path="$(podman machine inspect --format '{{.ConnectionInfo.PodmanSocket.Path}}')"
  export DOCKER_HOST="unix://${socket_path}"

  # Add provider only if missing.
  # Why:
  # - Makes reruns safer/idempotent
  if devpod provider list 2>/dev/null | grep -qE '(^|[[:space:]])docker([[:space:]]|$)'; then
    log "DevPod docker provider already present."
  else
    log "Adding DevPod docker provider"
    run "devpod provider add docker"
  fi

  # Configure provider to use Podman.
  # Why:
  # - This is the central integration step
  # - DevPod continues to think in terms of a docker provider, but actually invokes Podman
  log "Configuring DevPod docker provider to use Podman"
  run "devpod provider use docker -o DOCKER_PATH=\"${PODMAN_BIN}\" -o DOCKER_HOST=\"${DOCKER_HOST}\""

  log "Current DevPod provider options:"
  run "devpod provider options docker"
}

########################################
# Validation
#
# Why this exists:
# - A setup script should prove the configuration works
# - Running a tiny Alpine container is a fast, high-signal validation
########################################

validate_runtime() {
  export PATH="/opt/podman/bin:$PATH"
  hash -r

  log "Validating Podman runtime with a simple Alpine container"
  run "podman run --rm docker.io/library/alpine:latest echo \"podman works\""
}

########################################
# Main
########################################

main() {
  log "Starting Podman + DevPod setup on macOS"
  log "Configuration:"
  log "  REMOVE_DOCKER_REMNANTS=${REMOVE_DOCKER_REMNANTS}"
  log "  PODMAN_BIN=${PODMAN_BIN}"
  log "  BASH_PROFILE=${BASH_PROFILE}"
  log "  DRY_RUN=${DRY_RUN}"

  require_file_executable "$PODMAN_BIN"
  require_cmd devpod

  if [[ "$REMOVE_DOCKER_REMNANTS" == "true" ]]; then
    remove_docker_remnants
  else
    log "Docker remnant cleanup disabled by parameter."
  fi

  configure_bash_profile
  initialize_and_start_podman_machine
  start_podman_system_service
  configure_devpod_for_podman
  validate_runtime

  cat <<EOF

============================================================
Setup complete
============================================================

What this script did:
- Optionally removed Docker Desktop remnants
- Added Podman to your bash PATH
- Persisted a Docker-compatible DOCKER_HOST for future shells
- Added an interactive 'docker=podman' alias to bash
- Initialized/started Podman machine
- Started Podman system service
- Configured DevPod's docker provider to use Podman
- Validated Podman by running a test container

Recommended next steps:
1. Reload your bash profile in your current shell:
     source "${BASH_PROFILE}"

2. Verify:
     which podman
     podman info
     devpod provider list
     devpod provider options docker

3. Test a DevPod workspace:
     devpod up github.com/microsoft/vscode-remote-try-node --ide none

Useful notes:
- Podman service log:
     /tmp/podman-system-service.log

- If you reboot, you may need:
     podman machine start

- If a tool expects 'docker' interactively, your bash alias should help:
     docker ps

- DevPod itself is configured explicitly through provider settings and does not rely on the alias.

EOF
}

main "$@"
