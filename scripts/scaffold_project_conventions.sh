#!/usr/bin/env bash
set -euo pipefail

asset_root="/usr/local/share/polyglot-devcontainers/starter-scaffold"
template_name="${1:-${POLYGLOT_BOOTSTRAP_TEMPLATE:-starter}}"
project_name="$(basename "${PWD}")"
project_slug="$(
  printf '%s' "${project_name}" \
    | tr '[:upper:]' '[:lower:]' \
    | sed -E 's/[^a-z0-9._-]+/-/g; s/^-+//; s/-+$//'
)"

escape_sed_replacement() {
  printf '%s' "$1" | sed -e 's/[\/&]/\\&/g'
}

copy_if_missing() {
  local source="$1"
  local destination="$2"

  if [[ -e "${destination}" ]]; then
    return 0
  fi

  mkdir -p "$(dirname "${destination}")"
  cp "${source}" "${destination}"
}

render_agents_file() {
  local source="${asset_root}/AGENTS.md.template"
  local destination="AGENTS.md"
  local escaped_project_name
  local escaped_project_slug
  local escaped_template_name

  if [[ -e "${destination}" ]]; then
    return 0
  fi

  escaped_project_name="$(escape_sed_replacement "${project_name}")"
  escaped_project_slug="$(escape_sed_replacement "${project_slug}")"
  escaped_template_name="$(escape_sed_replacement "${template_name}")"

  mkdir -p "$(dirname "${destination}")"
  sed \
    -e "s/__PROJECT_NAME__/${escaped_project_name}/g" \
    -e "s/__PROJECT_SLUG__/${escaped_project_slug}/g" \
    -e "s/__STARTER_TEMPLATE__/${escaped_template_name}/g" \
    "${source}" > "${destination}"
}

main() {
  if [[ ! -d "${asset_root}" ]]; then
    echo "Starter scaffold assets not found: ${asset_root}" >&2
    exit 1
  fi

  render_agents_file

  mkdir -p .kbriefs/templates
  mkdir -p \
    docs/tutorials \
    docs/how-to \
    docs/reference \
    docs/reference/testing \
    docs/explanation \
    docs/explanation/decisions

  copy_if_missing "${asset_root}/.kbriefs/README.md" ".kbriefs/README.md"

  while IFS= read -r template; do
    copy_if_missing "${template}" ".kbriefs/templates/$(basename "${template}")"
  done < <(find "${asset_root}/.kbriefs/templates" -maxdepth 1 -type f | sort)

  copy_if_missing "${asset_root}/docs/README.md" "docs/README.md"
  copy_if_missing "${asset_root}/docs/tutorials/README.md" "docs/tutorials/README.md"
  copy_if_missing "${asset_root}/docs/how-to/README.md" "docs/how-to/README.md"
  copy_if_missing "${asset_root}/docs/reference/README.md" "docs/reference/README.md"
  copy_if_missing "${asset_root}/docs/reference/testing/README.md" "docs/reference/testing/README.md"
  copy_if_missing "${asset_root}/docs/explanation/README.md" "docs/explanation/README.md"
  copy_if_missing "${asset_root}/docs/explanation/decisions/README.md" "docs/explanation/decisions/README.md"
}

main "$@"
