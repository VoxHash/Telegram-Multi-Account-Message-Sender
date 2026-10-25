#!/usr/bin/env bash
# Assemble a Windows release directory from a PyInstaller EXE + install.ps1.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

BINARY_PATH="${1:-}"
OUTPUT_DIR="${2:-}"
VERSION="${3:-}"

if [[ -z "${BINARY_PATH}" || -z "${OUTPUT_DIR}" ]]; then
  echo "Usage: $0 <pyinstaller-exe> <output-dir> [version]" >&2
  exit 1
fi

if [[ ! -f "${BINARY_PATH}" ]]; then
  echo "error: binary not found: ${BINARY_PATH}" >&2
  exit 1
fi

rm -rf "${OUTPUT_DIR}"
mkdir -p "${OUTPUT_DIR}"

cp "${BINARY_PATH}" "${OUTPUT_DIR}/telegram-multi-account-sender.exe"
cp "${SCRIPT_DIR}/install.ps1" "${OUTPUT_DIR}/install.ps1"

if [[ -f "${REPO_ROOT}/assets/icons/favicon.ico" ]]; then
  cp "${REPO_ROOT}/assets/icons/favicon.ico" "${OUTPUT_DIR}/favicon.ico"
fi

cat > "${OUTPUT_DIR}/INSTALL.txt" <<EOF
Telegram Multi-Account Message Sender${VERSION:+ (${VERSION})} — Windows distribution

1. Extract this archive to a folder of your choice.
2. From that folder, run PowerShell (no admin required):

     powershell -ExecutionPolicy Bypass -File .\\install.ps1

3. Launch:

     %LOCALAPPDATA%\\Programs\\TelegramMultiAccountSender\\telegram-multi-account-sender.exe

File association: double-click *.tmas-backup.zip to open a local restore prompt
(after install registers ProgID dev.voxhash.tmas-backup under HKCU).

Portable / associate-only (no copy):

     powershell -ExecutionPolicy Bypass -File .\\install.ps1 -ExePath ".\\telegram-multi-account-sender.exe"

Uninstall:

     powershell -ExecutionPolicy Bypass -File .\\install.ps1 -Uninstall

Standalone EXE (without install.ps1) still runs; file association requires this installer.

Docs: https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender/blob/main/docs/installation.md
EOF

echo "Assembled Windows dist at ${OUTPUT_DIR}"
