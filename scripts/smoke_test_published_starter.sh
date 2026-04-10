#!/usr/bin/env bash
set -euo pipefail

image=""
run_scenarios=0
attempts="${POLYGLOT_SMOKE_ATTEMPTS:-2}"

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

write_devcontainer_placeholder() {
  local workspace="$1"

  mkdir -p "${workspace}/.devcontainer"
  chmod -R 0777 "${workspace}"
  cat > "${workspace}/.devcontainer/devcontainer.json" <<'EOF'
{
  "name": "bootstrap-smoke-test"
}
EOF
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
echo "[starter-smoke] phase=task-ci"
task ci
EOF
}

run_attempt() {
  local attempt="$1"
  local workspace
  local command

  workspace="$(mktemp -d)"
  trap 'rm -rf "'"${workspace}"'" >/dev/null 2>&1 || true' RETURN
  write_devcontainer_placeholder "${workspace}"

  command="$(build_container_command)"
  if [[ "${run_scenarios}" -eq 1 ]]; then
    command+=$'\n'
    command+='echo "[starter-smoke] phase=scenarios-verify"'
    command+=$'\n'
    command+='task scenarios:verify'
  fi

  echo "[starter-smoke] attempt=${attempt}/${attempts} image=${image}" >&2
  if docker run --rm \
    -v "${workspace}:/workspaces/project" \
    -w /workspaces/project \
    "${image}" \
    bash -lc "${command}"
  then
    return 0
  fi

  echo "[starter-smoke] attempt=${attempt}/${attempts} failed" >&2
  workspace_diagnostics "${workspace}"
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
