#!/usr/bin/env bash
set -euo pipefail

rm -f /etc/apt/sources.list.d/yarn.list
apt-get update
apt-get install -y --no-install-recommends fd-find jq ripgrep shellcheck
rm -rf /var/lib/apt/lists/*
