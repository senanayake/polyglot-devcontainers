#!/usr/bin/env bash
set -euo pipefail

image=""
run_scenarios=0
attempts="${POLYGLOT_SMOKE_ATTEMPTS:-2}"
workspace_override=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image)
      image="${2:?missing image value}"
      shift 2
      ;;
    --run-scenarios)
      run_scenarios=1
      shift
      ;;
    --workspace)
      workspace_override="${2:?missing workspace value}"
      shift 2
      ;;
    *)
      echo "Unknown argument: $1" >&2
      exit 2
      ;;
  esac
done

if [[ -z "${image}" ]]; then
  echo "--image is required" >&2
  exit 2
fi

if ! [[ "${attempts}" =~ ^[0-9]+$ ]] || [[ "${attempts}" -lt 1 ]]; then
  echo "POLYGLOT_SMOKE_ATTEMPTS must be a positive integer" >&2
  exit 2
fi

resolve_python() {
  if [[ -n "${PYTHON:-}" ]]; then
    if [[ -x "${PYTHON}" ]]; then
      printf '%s\n' "${PYTHON}"
      return 0
    fi

    if command -v cygpath >/dev/null 2>&1; then
      local converted_python
      converted_python="$(cygpath -u "${PYTHON}")"
      if [[ -x "${converted_python}" ]]; then
        printf '%s\n' "${converted_python}"
        return 0
      fi
    fi
  fi

  if command -v python >/dev/null 2>&1; then
    printf '%s\n' python
    return 0
  fi

  if command -v python3 >/dev/null 2>&1; then
    printf '%s\n' python3
    return 0
  fi

  echo "python or python3 is required to run the published-image smoke test" >&2
  return 1
}

python_bin="$(resolve_python)"

write_devcontainer_placeholder() {
  local workspace="$1"

  mkdir -p "${workspace}/.devcontainer"
  cat > "${workspace}/.devcontainer/devcontainer.json" <<'EOF'
{
  "name": "bootstrap-smoke-test"
}
EOF
  chmod -R 0777 "${workspace}"
}

normalize_workspace_permissions() {
  local workspace="$1"

  mkdir -p "${workspace}"
  # The image-backed proof path can hand us a pre-generated workspace created
  # by a different container/user. Normalize it before bind-mounting into the
  # nested smoke container so `task init` can scaffold into it.
  chmod -R 0777 "${workspace}"
}

workspace_diagnostics() {
  local workspace="$1"

  echo "[starter-smoke] workspace=${workspace}" >&2
  echo "[starter-smoke] top-level contents:" >&2
  find "${workspace}" -mindepth 1 -maxdepth 2 -printf '  %P\n' | sort >&2 || true

  if [[ -f "${workspace}/.polyglot-bootstrap.json" ]]; then
    echo "[starter-smoke] bootstrap marker:" >&2
    cat "${workspace}/.polyglot-bootstrap.json" >&2 || true
  fi

  if [[ -d "${workspace}/.artifacts" ]]; then
    echo "[starter-smoke] artifact contents:" >&2
    find "${workspace}/.artifacts" -mindepth 1 -maxdepth 3 -printf '  %P\n' | sort >&2 || true
  fi
}

build_container_command() {
  cat <<'EOF'
set -euo pipefail
echo "[starter-smoke] phase=man-polyglot"
man polyglot >/dev/null
echo "[starter-smoke] phase=man-polyglot-scenarios"
man polyglot-scenarios >/dev/null
echo "[starter-smoke] phase=task-init"
task init
echo "[starter-smoke] phase=verify-bootstrap"
test -f Taskfile.yml
test -f .polyglot-bootstrap.json
echo "[starter-smoke] phase=verify-project-conventions"
test -f AGENTS.md
grep -q "Knowledge-Based Product Development" AGENTS.md
test -f .kbriefs/README.md
test -f .kbriefs/templates/design-space.md
test -f .kbriefs/templates/failure-mode.md
test -f .kbriefs/templates/limit.md
test -f .kbriefs/templates/source-profile.md
test -f .kbriefs/templates/standard.md
test -f .kbriefs/templates/tradeoff.md
test -f docs/README.md
test -f docs/tutorials/README.md
test -f docs/how-to/README.md
test -f docs/reference/README.md
test -f docs/explanation/README.md
echo "[starter-smoke] phase=task-ci"
task ci
EOF
}

run_attempt() {
  local attempt="$1"
  local workspace
  local command
  local cleanup_workspace=1

  if [[ -n "${workspace_override}" ]]; then
    workspace="${workspace_override}"
    cleanup_workspace=0
    normalize_workspace_permissions "${workspace}"
  else
    workspace="$(mktemp -d)"
    trap 'rm -rf "'"${workspace}"'" >/dev/null 2>&1 || true' RETURN
    write_devcontainer_placeholder "${workspace}"
  fi

  command="$(build_container_command)"
  if [[ "${run_scenarios}" -eq 1 ]]; then
    command+=$'\n'
    command+='echo "[starter-smoke] phase=scenarios-verify"'
    command+=$'\n'
    command+='task scenarios:verify'
  fi

  echo "[starter-smoke] attempt=${attempt}/${attempts} image=${image}" >&2
  if "${python_bin}" scripts/oci_runtime.py run --rm \
    -v "${workspace}:/workspaces/project" \
    -w /workspaces/project \
    "${image}" \
    bash -lc "${command}"
  then
    return 0
  fi

  echo "[starter-smoke] attempt=${attempt}/${attempts} failed" >&2
  workspace_diagnostics "${workspace}"
  if [[ "${cleanup_workspace}" -eq 0 ]]; then
    echo "[starter-smoke] preserved workspace=${workspace}" >&2
  fi
  return 1
}

for attempt in $(seq 1 "${attempts}"); do
  if run_attempt "${attempt}"; then
    exit 0
  fi

  if [[ "${attempt}" -lt "${attempts}" ]]; then
    echo "[starter-smoke] retrying with a fresh workspace" >&2
    sleep 2
  fi
done

exit 1
