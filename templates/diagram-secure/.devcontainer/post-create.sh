#!/usr/bin/env bash
set -euo pipefail

if [[ -f "scripts/install_runtime_docs.sh" && -d "man/man7" ]]; then
  bash scripts/install_runtime_docs.sh man/man7
fi

if [[ -f "Taskfile.yml" || -f "Taskfile.yaml" ]]; then
  task init
fi
