#!/usr/bin/env bash
set -euo pipefail

template="${POLYGLOT_BOOTSTRAP_TEMPLATE:-}"
payload="/usr/local/share/polyglot-devcontainers/bootstrap/${template}"

if [[ -z "${template}" ]]; then
  echo "No workspace bootstrap template is configured for this image." >&2
  exit 1
fi

if [[ ! -d "${payload}" ]]; then
  echo "Bootstrap payload not found: ${payload}" >&2
  exit 1
fi

while IFS= read -r -d '' entry; do
  name="$(basename "${entry}")"
  case "${name}" in
    .git|.gitignore|.devcontainer|.editorconfig|.vscode)
      ;;
    *)
      echo "Refusing to scaffold into a non-empty workspace; found ${name}." >&2
      exit 1
      ;;
  esac
done < <(find . -mindepth 1 -maxdepth 1 -print0)

cp -R "${payload}/." .
/usr/local/bin/polyglot-scaffold-project-conventions "${template}"

cat > .polyglot-bootstrap.json <<EOF
{
  "template": "${template}",
  "project_conventions_scaffolded": true
}
EOF
