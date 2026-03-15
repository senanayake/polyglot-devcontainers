#!/usr/bin/env bash
set -euo pipefail

GRADLE_VERSION="9.1.0"

apt-get update
apt-get install -y --no-install-recommends ca-certificates curl gnupg unzip
rm -rf /var/lib/apt/lists/*

curl -fsSL "https://services.gradle.org/distributions/gradle-${GRADLE_VERSION}-bin.zip" -o /tmp/gradle.zip
rm -rf "/opt/gradle-${GRADLE_VERSION}"
unzip -q /tmp/gradle.zip -d /opt
ln -sf "/opt/gradle-${GRADLE_VERSION}/bin/gradle" /usr/local/bin/gradle
rm -f /tmp/gradle.zip

mkdir -p /usr/share/keyrings
curl -fsSL https://get.trivy.dev/deb/public.key \
  | gpg --dearmor -o /usr/share/keyrings/trivy.gpg
echo "deb [signed-by=/usr/share/keyrings/trivy.gpg] https://get.trivy.dev/deb generic main" \
  > /etc/apt/sources.list.d/trivy.list
apt-get update
apt-get install -y --no-install-recommends trivy
rm -rf /var/lib/apt/lists/*
