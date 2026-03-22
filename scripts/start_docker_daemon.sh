#!/usr/bin/env bash
set -euo pipefail

if docker info >/dev/null 2>&1; then
  exit 0
fi

if ! command -v dockerd >/dev/null 2>&1; then
  echo "[maintainer-runtime] dockerd is not installed in the maintainer container" >&2
  exit 1
fi

if pgrep -x dockerd >/dev/null 2>&1; then
  for _ in $(seq 1 30); do
    if docker info >/dev/null 2>&1; then
      exit 0
    fi
    sleep 1
  done
fi

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

LOG_FILE="${POLYGLOT_DOCKERD_LOG:-/tmp/polyglot-dockerd.log}"
STORAGE_DRIVER="${POLYGLOT_DOCKER_STORAGE_DRIVER:-vfs}"

${SUDO} mkdir -p /var/lib/docker
${SUDO} sh -c "nohup dockerd --host=unix:///var/run/docker.sock --storage-driver=${STORAGE_DRIVER} >'${LOG_FILE}' 2>&1 &"

for _ in $(seq 1 60); do
  if docker info >/dev/null 2>&1; then
    echo "[maintainer-runtime] docker daemon ready" >&2
    exit 0
  fi
  sleep 1
done

echo "[maintainer-runtime] docker daemon did not become ready; log follows" >&2
${SUDO} tail -n 200 "${LOG_FILE}" >&2 || true
exit 1
