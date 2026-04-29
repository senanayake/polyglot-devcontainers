#!/usr/bin/env bash
set -euo pipefail

TASK_VERSION="3.50.0"
GITLEAKS_VERSION="8.30.1"

rm -f /etc/apt/sources.list.d/yarn.list
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl git tar
rm -rf /var/lib/apt/lists/*

arch="$(dpkg --print-architecture)"
case "${arch}" in
  amd64)
    task_archive="task_linux_amd64.tar.gz"
    gitleaks_archive="gitleaks_${GITLEAKS_VERSION}_linux_x64.tar.gz"
    ;;
  arm64)
    task_archive="task_linux_arm64.tar.gz"
    gitleaks_archive="gitleaks_${GITLEAKS_VERSION}_linux_arm64.tar.gz"
    ;;
  *)
    echo "Unsupported architecture: ${arch}" >&2
    exit 1
    ;;
esac

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/${task_archive}" "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/${task_archive}"
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/task_checksums.txt" "https://github.com/go-task/task/releases/download/v${TASK_VERSION}/task_checksums.txt"
sed -n "s#  ${task_archive}\$#  ${tmpdir}/${task_archive}#p" "${tmpdir}/task_checksums.txt" | sha256sum -c -
tar -xzf "${tmpdir}/${task_archive}" -C /usr/local/bin task

curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/${gitleaks_archive}" "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/${gitleaks_archive}"
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/gitleaks_checksums.txt" "https://github.com/gitleaks/gitleaks/releases/download/v${GITLEAKS_VERSION}/gitleaks_${GITLEAKS_VERSION}_checksums.txt"
sed -n "s#  ${gitleaks_archive}\$#  ${tmpdir}/${gitleaks_archive}#p" "${tmpdir}/gitleaks_checksums.txt" | sha256sum -c -
tar -xzf "${tmpdir}/${gitleaks_archive}" -C /usr/local/bin gitleaks
chmod +x /usr/local/bin/gitleaks
