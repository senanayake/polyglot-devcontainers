#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
artifact_dir="${repo_root}/.artifacts/scenarios"
log_path="${artifact_dir}/java-openrewrite-dry-run.log"
patch_artifact="${artifact_dir}/java-openrewrite-dry-run.patch"

mkdir -p "${artifact_dir}"
rm -f "${log_path}" "${patch_artifact}"

sandbox_root="$(mktemp -d /tmp/polyglot-openrewrite-proof.XXXXXX)"
cleanup() {
  rm -rf "${sandbox_root}"
}
trap cleanup EXIT

mkdir -p "${sandbox_root}/examples/java-maintenance-example" "${sandbox_root}/scripts"
cp -a "${repo_root}/examples/java-maintenance-example/." "${sandbox_root}/examples/java-maintenance-example/"
cp "${repo_root}/scripts/require_maintainer_container.py" "${sandbox_root}/scripts/"
cp "${repo_root}/scripts/oci_runtime.py" "${sandbox_root}/scripts/"

target_file="${sandbox_root}/examples/java-maintenance-example/src/main/java/dev/polyglot/maintenance/DependencyPlanSummary.java"
if ! grep -Fq 'import java.time.Instant;' "${target_file}"; then
  sed -i '/import com\.fasterxml\.jackson\.databind\.ObjectMapper;/a import java.time.Instant;' "${target_file}"
fi

tmp_log="$(mktemp /tmp/polyglot-openrewrite-proof-log.XXXXXX)"
export GRADLE_USER_HOME="/tmp/gradle-openrewrite-proof-home"

(
  set -x
  cd "${sandbox_root}/examples/java-maintenance-example"
  task rewrite:dry-run
) | tee "${tmp_log}"

patch_path="${sandbox_root}/examples/java-maintenance-example/build/reports/rewrite/rewrite.patch"
if [[ ! -f "${patch_path}" ]]; then
  echo "expected rewrite patch at ${patch_path}" | tee -a "${tmp_log}"
  exit 1
fi

if ! grep -Fq 'import java.time.Instant;' "${patch_path}"; then
  echo "expected injected unused import to appear in dry-run patch" | tee -a "${tmp_log}"
  exit 1
fi

if ! grep -Fq 'import java.time.Instant;' "${target_file}"; then
  echo "rewrite:dry-run unexpectedly modified source files" | tee -a "${tmp_log}"
  exit 1
fi

{
  cat "${tmp_log}"
  echo
  echo "validated_patch=${patch_path}"
  echo "result=rewrite:dry-run generated a patch and left source files unchanged"
} > "${log_path}"
cp "${patch_path}" "${patch_artifact}"
rm -f "${tmp_log}"
