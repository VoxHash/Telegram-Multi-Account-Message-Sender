#!/usr/bin/env bash
# Assemble a Linux release directory from a PyInstaller binary + packaging metadata.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BINARY_PATH="${1:-}"
OUTPUT_DIR="${2:-}"
VERSION="${3:-}"

if [[ -z "${BINARY_PATH}" || -z "${OUTPUT_DIR}" ]]; then
  echo "Usage: $0 <pyinstaller-binary> <output-dir> [version]" >&2
  exit 1
fi

if [[ ! -f "${BINARY_PATH}" ]]; then
  echo "error: binary not found: ${BINARY_PATH}" >&2
  exit 1
fi

rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}/icons"

install -m 755 "${BINARY_PATH}" "${OUTPUT_DIR}/telegram-multi-account-sender"
install -m 755 "${SCRIPT_DIR}/install.sh" "${OUTPUT_DIR}/install.sh"
install -m 644 "${SCRIPT_DIR}/dev.voxhash.telegram-multi-account-sender.desktop" \
  "${OUTPUT_DIR}/dev.voxhash.telegram-multi-account-sender.desktop"
install -m 644 "${SCRIPT_DIR}/application-x-tmas-backup.xml" \
  "${OUTPUT_DIR}/application-x-tmas-backup.xml"

for icon in "${REPO_ROOT}/assets/icons/"telegram-multiaccount-sender_*.png; do
  install -m 644 "${icon}" "${OUTPUT_DIR}/icons/"
done

cat > "${OUTPUT_DIR}/INSTALL.txt" <<EOF
Telegram Multi-Account Message Sender${VERSION:+ (${VERSION})} — Linux distribution

1. Extract this archive.
2. From this directory run:
     ./install.sh
3. Launch from your application menu, or:
     ~/.local/bin/telegram-multi-account-sender

File association: double-click *.tmas-backup.zip to open a local restore prompt
(after install registers application/x-tmas-backup).

Uninstall:
  ./install.sh --uninstall

Docs: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/blob/main/docs/installation.md
EOF

echo "Assembled Linux dist at ${OUTPUT_DIR}"
