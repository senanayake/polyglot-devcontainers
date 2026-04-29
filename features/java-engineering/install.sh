#!/usr/bin/env bash
set -euo pipefail

GRADLE_VERSION="9.1.0"
TRIVY_APT_KEYRING="/usr/share/keyrings/trivy.gpg"
TRIVY_APT_REPO="https://aquasecurity.github.io/trivy-repo/deb"
TRIVY_APT_KEY_URL="${TRIVY_APT_REPO}/public.key"

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg unzip
rm -rf /var/lib/apt/lists/*

curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo /tmp/gradle.zip "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo /tmp/gradle.zip.sha256 "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip.sha256"
echo "$(cat /tmp/gradle.zip.sha256)  /tmp/gradle.zip" | sha256sum -c -
rm -rf "/opt/gradle-${GRADLE_VERSION}"
unzip -q /tmp/gradle.zip -d /opt
ln -sf "/opt/gradle-${GRADLE_VERSION}/bin/gradle" /usr/local/bin/gradle
rm -f /tmp/gradle.zip /tmp/gradle.zip.sha256

mkdir -p /usr/share/keyrings
# Follow Trivy's current Debian install instructions instead of pinning the
# raw key file bytes, which can rotate without a package-signing trust change.
curl --retry 5 --retry-all-errors --retry-delay 2 -fsSL "${TRIVY_APT_KEY_URL}" | gpg --dearmor --batch --yes -o "${TRIVY_APT_KEYRING}"
echo "deb [signed-by=${TRIVY_APT_KEYRING}] ${TRIVY_APT_REPO} generic main" \
  > /etc/apt/sources.list.d/trivy.list
apt-get update
apt-get install -y --no-install-recommends trivy
rm -rf /var/lib/apt/lists/*
