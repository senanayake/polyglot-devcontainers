#!/usr/bin/env bash
set -euo pipefail

texlive="${TEXLIVE:-false}"

apt-get update
apt-get install -y --no-install-recommends pandoc

if [[ "${texlive}" == "true" ]]; then
  apt-get install -y --no-install-recommends texlive-latex-recommended texlive-xetex
fi

rm -rf /var/lib/apt/lists/*
