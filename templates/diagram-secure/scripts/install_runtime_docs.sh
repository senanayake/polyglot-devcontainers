#!/usr/bin/env bash
set -euo pipefail

SOURCE_DIR="${1:-man/man7}"
TARGET_DIR="/usr/local/share/man/man7"

if [[ "${EUID}" -eq 0 ]]; then
  SUDO=""
else
  SUDO="sudo"
fi

if ! command -v man >/dev/null 2>&1; then
  ${SUDO} apt-get update
  ${SUDO} apt-get install -y --no-install-recommends man-db less
fi

if [[ ! -d "${SOURCE_DIR}" ]]; then
  echo "runtime docs source directory not found: ${SOURCE_DIR}" >&2
  exit 1
fi

${SUDO} mkdir -p "${TARGET_DIR}"
${SUDO} cp -f "${SOURCE_DIR}"/*.7 "${TARGET_DIR}/"
${SUDO} mandb -q || true
