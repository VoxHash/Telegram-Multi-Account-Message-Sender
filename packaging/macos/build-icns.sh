#!/usr/bin/env bash
# Build a real AppIcon.icns from PNG sources. Requires macOS iconutil.
# Linux/CI without macOS: packaging/macos/AppIcon.png is used as a fallback icon source.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"
ICONSET="${SCRIPT_DIR}/AppIcon.iconset"
OUT_ICNS="${SCRIPT_DIR}/AppIcon.icns"
SRC_DIR="${REPO_ROOT}/assets/icons"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "build-icns.sh requires macOS (iconutil). Skipping; using AppIcon.png fallback." >&2
  exit 0
fi

if ! command -v iconutil >/dev/null 2>&1; then
  echo "error: iconutil not found" >&2
  exit 1
fi

rm -rf "${ICONSET}"
mkdir -p "${ICONSET}"

copy_size() {
  local src_size="$1"
  local dest_name="$2"
  local src="${SRC_DIR}/telegram-multiaccount-sender_${src_size}.png"
  if [[ ! -f "${src}" ]]; then
    echo "error: missing ${src}" >&2
    exit 1
  fi
  cp "${src}" "${ICONSET}/${dest_name}"
}

copy_size 16 icon_16x16.png
copy_size 32 icon_16x16@2x.png
copy_size 32 icon_32x32.png
copy_size 64 icon_32x32@2x.png
copy_size 128 icon_128x128.png
# 192 ≈ 128@1.5; use 256 for @2x of 128
copy_size 256 icon_128x128@2x.png
copy_size 256 icon_256x256.png
copy_size 512 icon_256x256@2x.png
copy_size 512 icon_512x512.png
copy_size 1024 icon_512x512@2x.png

iconutil -c icns "${ICONSET}" -o "${OUT_ICNS}"
rm -rf "${ICONSET}"
echo "Wrote ${OUT_ICNS}"
