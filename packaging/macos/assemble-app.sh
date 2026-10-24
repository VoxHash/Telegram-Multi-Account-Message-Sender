#!/usr/bin/env bash
# Wrap a PyInstaller binary (or .app) into a proper .app with Info.plist + document types.
# Intended for macOS runners; on other hosts this script exits with a clear message.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERSION="${3:-1.2.23}"
SRC="${1:-}"
OUT_APP="${2:-}"

if [[ -z "${SRC}" || -z "${OUT_APP}" ]]; then
  echo "Usage: $0 <dist-binary-or-app> <output.app> [version]" >&2
  exit 1
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "assemble-app.sh must run on macOS (creates .app / DMG inputs)." >&2
  exit 1
fi

rm -rf "${OUT_APP}"
mkdir -p "${OUT_APP}/Contents/MacOS" "${OUT_APP}/Contents/Resources"

if [[ -d "${SRC}" && "${SRC}" == *.app ]]; then
  # Copy existing PyInstaller .app contents, then overlay Info.plist
  cp -R "${SRC}/Contents/MacOS/." "${OUT_APP}/Contents/MacOS/"
  if [[ -d "${SRC}/Contents/Resources" ]]; then
    cp -R "${SRC}/Contents/Resources/." "${OUT_APP}/Contents/Resources/" 2>/dev/null || true
  fi
elif [[ -f "${SRC}" ]]; then
  install -m 755 "${SRC}" "${OUT_APP}/Contents/MacOS/telegram-multi-account-sender"
else
  echo "error: source not found: ${SRC}" >&2
  exit 1
fi

# Ensure executable name matches Info.plist CFBundleExecutable
if [[ ! -f "${OUT_APP}/Contents/MacOS/telegram-multi-account-sender" ]]; then
  first_bin="$(find "${OUT_APP}/Contents/MacOS" -type f -perm -111 | head -n1 || true)"
  if [[ -n "${first_bin}" ]]; then
    mv "${first_bin}" "${OUT_APP}/Contents/MacOS/telegram-multi-account-sender"
  fi
fi

plutil -replace CFBundleShortVersionString -string "${VERSION#v}" "${SCRIPT_DIR}/Info.plist" 2>/dev/null || true
plutil -replace CFBundleVersion -string "${VERSION#v}" "${SCRIPT_DIR}/Info.plist" 2>/dev/null || true
# Prefer a copy so we do not mutate the template when plutil is unavailable
sed "s/<string>1\\.2\\.[0-9][0-9]*<\\/string>/<string>${VERSION#v}<\\/string>/g" \
  "${SCRIPT_DIR}/Info.plist" > "${OUT_APP}/Contents/Info.plist"

if [[ -f "${SCRIPT_DIR}/AppIcon.icns" ]]; then
  cp "${SCRIPT_DIR}/AppIcon.icns" "${OUT_APP}/Contents/Resources/AppIcon.icns"
elif [[ -f "${SCRIPT_DIR}/AppIcon.png" ]]; then
  cp "${SCRIPT_DIR}/AppIcon.png" "${OUT_APP}/Contents/Resources/AppIcon.png"
fi

echo "Assembled ${OUT_APP}"
