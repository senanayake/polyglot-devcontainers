#!/usr/bin/env bash
set -euo pipefail

if [[ -f "Taskfile.yml" || -f "Taskfile.yaml" ]]; then
  task init
fi

if [[ -f ".pre-commit-config.yaml" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pre-commit install
fi
