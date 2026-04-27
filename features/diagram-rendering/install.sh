#!/usr/bin/env bash
set -euo pipefail

D2_VERSION="0.7.1"
D2_SHA256_AMD64="eb172adf59f38d1e5a70ab177591356754ffaf9bebb84e0ca8b767dfb421dad7"
D2_SHA256_ARM64="ce3a0b985a8f91335a826c254b3a88736fd81afcdd08b58f6c749d2add6864b0"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
FONT_TARGET_DIR="/usr/local/share/polyglot-devcontainers/fonts"

pick_font() {
  local destination="$1"
  shift

  local pattern=""
  local candidate=""
  for pattern in "$@"; do
    candidate="$(find /usr/share/fonts -type f -iname "${pattern}" | sort | head -n 1 || true)"
    if [[ -n "${candidate}" ]]; then
      ln -sf "${candidate}" "${FONT_TARGET_DIR}/${destination}"
      return 0
    fi
  done

  echo "Unable to find a usable font for ${destination}" >&2
  exit 1
}

rm -f /etc/apt/sources.list.d/yarn.list
apt-get update
apt-get install -y --no-install-recommends ca-certificates curl fonts-inter fonts-liberation2 fonts-noto-core fonts-noto-mono graphviz jq tar
rm -rf /var/lib/apt/lists/*

arch="$(dpkg --print-architecture)"
case "${arch}" in
  amd64)
    d2_archive="d2-v${D2_VERSION}-linux-amd64.tar.gz"
    d2_sha256="${D2_SHA256_AMD64}"
    ;;
  arm64)
    d2_archive="d2-v${D2_VERSION}-linux-arm64.tar.gz"
    d2_sha256="${D2_SHA256_ARM64}"
    ;;
  *)
    echo "Unsupported architecture: ${arch}" >&2
    exit 1
    ;;
esac

tmpdir="$(mktemp -d)"
trap 'rm -rf "${tmpdir}"' EXIT

curl --retry 5 --retry-all-errors --retry-delay 2 -fsSLo "${tmpdir}/${d2_archive}" "https://github.com/terrastruct/d2/releases/download/v${D2_VERSION}/${d2_archive}"
echo "${d2_sha256}  ${tmpdir}/${d2_archive}" | sha256sum -c -
tar -xzf "${tmpdir}/${d2_archive}" -C "${tmpdir}"
install -m 0755 "${tmpdir}/d2-v${D2_VERSION}/bin/d2" /usr/local/bin/d2
install -m 0755 "${SCRIPT_DIR}/diagram" /usr/local/bin/diagram

mkdir -p "${FONT_TARGET_DIR}"
pick_font regular.ttf "NotoSans-Regular.ttf" "LiberationSans-Regular.ttf" "DejaVuSans.ttf" "Inter-Regular.ttf"
pick_font italic.ttf "NotoSans-Italic.ttf" "LiberationSans-Italic.ttf" "DejaVuSans-Oblique.ttf" "Inter-Italic.ttf"
pick_font bold.ttf "NotoSans-Bold.ttf" "LiberationSans-Bold.ttf" "DejaVuSans-Bold.ttf" "Inter-Bold.ttf"
pick_font semibold.ttf "NotoSans-SemiBold.ttf" "NotoSans-Bold.ttf" "LiberationSans-Bold.ttf" "DejaVuSans-Bold.ttf" "Inter-Bold.ttf"
pick_font mono.ttf "NotoSansMono-Regular.ttf" "LiberationMono-Regular.ttf"
pick_font mono-bold.ttf "NotoSansMono-Bold.ttf" "LiberationMono-Bold.ttf"
pick_font mono-italic.ttf "LiberationMono-Italic.ttf" "NotoSansMono-Regular.ttf" "LiberationMono-Regular.ttf"
pick_font mono-semibold.ttf "NotoSansMono-Bold.ttf" "LiberationMono-Bold.ttf"
