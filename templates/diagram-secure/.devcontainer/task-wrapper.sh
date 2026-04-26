#!/usr/bin/env bash
set -euo pipefail

real_task="/usr/local/libexec/polyglot-devcontainers/task-real"

find_taskfile() {
  local dir="${PWD}"
  while true; do
    for candidate in Taskfile.yml Taskfile.yaml taskfile.yml taskfile.yaml; do
      if [[ -f "${dir}/${candidate}" ]]; then
        return 0
      fi
    done
    if [[ "${dir}" == "/" ]]; then
      return 1
    fi
    dir="$(dirname "${dir}")"
  done
}

print_bootstrap_hint() {
  echo "No Taskfile found in this workspace." >&2
  if [[ -n "${POLYGLOT_BOOTSTRAP_TEMPLATE:-}" ]]; then
    echo "Run 'task init' in an empty workspace to scaffold the ${POLYGLOT_BOOTSTRAP_TEMPLATE} starter." >&2
  fi
  echo "See 'man polyglot' for the top-level starter workflow." >&2
}

if find_taskfile; then
  exec "${real_task}" "$@"
fi

case "${1:-}" in
  "")
    print_bootstrap_hint
    exit 1
    ;;
  -h|--help|--version|--completion|--experiments)
    exec "${real_task}" "$@"
    ;;
  init)
    /usr/local/bin/polyglot-bootstrap-workspace
    exec "${real_task}" "$@"
    ;;
  *)
    exec "${real_task}" "$@"
    ;;
esac
