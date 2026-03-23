#!/usr/bin/env bash
set -euo pipefail

if [[ -f "scripts/install_runtime_docs.sh" && -d "man/man7" ]]; then
  bash scripts/install_runtime_docs.sh man/man7
fi

if [[ -f "Taskfile.yml" || -f "Taskfile.yaml" ]]; then
  task init
fi

if [[ -f ".pre-commit-config.yaml" ]] && git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  pre-commit install
fi
