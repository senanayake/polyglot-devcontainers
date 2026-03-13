#!/usr/bin/env bash
set -euo pipefail

TASK_VERSION="3.49.1"
GITLEAKS_VERSION="8.30.0"

rm -f /etc/apt/sources.list.d/yarn.list
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl git tar
rm -rf /var/lib/apt/lists/*

curl -sSL https://taskfile.dev/install.sh | sh -s -- -d -b /usr/local/bin "v${TASK_VERSION}"
curl -sSL "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz" \
  | tar -xz -C /usr/local/bin gitleaks
chmod +x /usr/local/bin/gitleaks
