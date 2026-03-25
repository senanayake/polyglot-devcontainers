#!/usr/bin/env bash
set -euo pipefail

image=""
run_scenarios=0

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

workspace="$(mktemp -d)"
cleanup() {
  rm -rf "${workspace}"
}
trap cleanup EXIT

mkdir -p "${workspace}/.devcontainer"
chmod -R 0777 "${workspace}"
cat > "${workspace}/.devcontainer/devcontainer.json" <<'EOF'
{
  "name": "bootstrap-smoke-test"
}
EOF

command='man polyglot >/dev/null && man polyglot-scenarios >/dev/null && task init && test -f Taskfile.yml && test -f .polyglot-bootstrap.json && task ci'
if [[ "${run_scenarios}" -eq 1 ]]; then
  command+=' && task scenarios:verify'
fi

docker run --rm \
  -u vscode \
  -v "${workspace}:/workspaces/project" \
  -w /workspaces/project \
  "${image}" \
  bash -lc "${command}"
