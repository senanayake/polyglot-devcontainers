#!/usr/bin/env bash
set -euo pipefail

GRADLE_VERSION="9.1.0"
TRIVY_KEY_SHA256="51ca5d1384095c462099add67e46b028e0df0ff741c0f95ad30f561c4fad1ad4" # gitleaks:allow

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg unzip
rm -rf /var/lib/apt/lists/*

curl -fsSLo /tmp/gradle.zip "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip"
curl -fsSLo /tmp/gradle.zip.sha256 "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip.sha256"
echo "$(cat /tmp/gradle.zip.sha256)  /tmp/gradle.zip" | sha256sum -c -
rm -rf "/opt/gradle-${GRADLE_VERSION}"
unzip -q /tmp/gradle.zip -d /opt
ln -sf "/opt/gradle-${GRADLE_VERSION}/bin/gradle" /usr/local/bin/gradle
rm -f /tmp/gradle.zip /tmp/gradle.zip.sha256

mkdir -p /usr/share/keyrings
curl -fsSLo /tmp/trivy.key https://get.trivy.dev/deb/public.key
echo "${TRIVY_KEY_SHA256}  /tmp/trivy.key" | sha256sum -c -
gpg --dearmor -o /usr/share/keyrings/trivy.gpg /tmp/trivy.key
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://get.trivy.dev/deb generic main" \
  > /etc/apt/sources.list.d/trivy.list
apt-get update
apt-get install -y --no-install-recommends trivy
rm -rf /var/lib/apt/lists/* /tmp/trivy.key
