#!/usr/bin/env bash
# Install the frozen Linux binary, desktop entry, icons, and .tmas-backup.zip MIME association
# for the current user (XDG paths under ~/.local). No root required.
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_DIR="${TMMS_BIN_DIR:-$HOME/.local/bin}"
APP_ID="dev.voxhash.telegram-multi-account-sender"
MIME_TYPE="application/x-tmas-backup"
DESKTOP_FILE="${APP_ID}.desktop"
MIME_FILE="application-x-tmas-backup.xml"

usage() {
  cat <<'EOF'
Usage: ./install.sh [--prefix DIR] [--bin-dir DIR] [--uninstall]

Installs telegram-multi-account-sender into the user XDG layout:
  ~/.local/bin/telegram-multi-account-sender
  ~/.local/share/applications/<app>.desktop
  ~/.local/share/mime/packages/application-x-tmas-backup.xml
  ~/.local/share/icons/hicolor/*/apps|mimetypes/...

Options:
  --prefix DIR    XDG data home (default: $XDG_DATA_HOME or ~/.local/share)
  --bin-dir DIR   Binary install directory (default: ~/.local/bin)
  --uninstall     Remove installed files and refresh desktop/MIME databases
EOF
}

uninstall() {
  rm -f "${BIN_DIR}/telegram-multi-account-sender"
  rm -f "${PREFIX}/applications/${DESKTOP_FILE}"
  rm -f "${PREFIX}/mime/packages/${MIME_FILE}"
  for size in 16 24 32 48 64 128 256 512; do
    rm -f "${PREFIX}/icons/hicolor/${size}x${size}/apps/${APP_ID}.png"
    rm -f "${PREFIX}/icons/hicolor/${size}x${size}/mimetypes/application-x-tmas-backup.png"
  done
  update-desktop-database "${PREFIX}/applications" 2>/dev/null || true
  update-mime-database "${PREFIX}/mime" 2>/dev/null || true
  echo "Uninstalled ${APP_ID} from ${PREFIX} and ${BIN_DIR}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --prefix)
      PREFIX="$2"
      shift 2
      ;;
    --bin-dir)
      BIN_DIR="$2"
      shift 2
      ;;
    --uninstall)
      uninstall
      exit 0
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
done

BINARY="${SCRIPT_DIR}/telegram-multi-account-sender"
if [[ ! -f "${BINARY}" ]]; then
  # Allow running from the repo packaging/linux tree against dist/
  if [[ -f "${SCRIPT_DIR}/../../dist/telegram-multi-account-sender" ]]; then
    BINARY="${SCRIPT_DIR}/../../dist/telegram-multi-account-sender"
  else
    echo "error: binary not found next to install.sh (expected telegram-multi-account-sender)" >&2
    echo "Assemble a release dir with packaging/linux/assemble-dist.sh first." >&2
    exit 1
  fi
fi

ICON_SRC="${SCRIPT_DIR}/icons"
if [[ ! -d "${ICON_SRC}" ]]; then
  REPO_ICONS="${SCRIPT_DIR}/../../assets/icons"
  if [[ -d "${REPO_ICONS}" ]]; then
    ICON_SRC="${REPO_ICONS}"
  else
    echo "error: icons directory not found" >&2
    exit 1
  fi
fi

DESKTOP_SRC="${SCRIPT_DIR}/${DESKTOP_FILE}"
MIME_SRC="${SCRIPT_DIR}/${MIME_FILE}"
if [[ ! -f "${DESKTOP_SRC}" || ! -f "${MIME_SRC}" ]]; then
  echo "error: desktop/MIME templates missing beside install.sh" >&2
  exit 1
fi

mkdir -p "${BIN_DIR}" "${PREFIX}/applications" "${PREFIX}/mime/packages"

install -m 755 "${BINARY}" "${BIN_DIR}/telegram-multi-account-sender"

# Rewrite Exec to the installed binary path so file associations work without PATH hacks.
tmp_desktop="$(mktemp)"
sed "s|^Exec=.*|Exec=${BIN_DIR}/telegram-multi-account-sender %f|" "${DESKTOP_SRC}" > "${tmp_desktop}"
install -m 644 "${tmp_desktop}" "${PREFIX}/applications/${DESKTOP_FILE}"
rm -f "${tmp_desktop}"

install -m 644 "${MIME_SRC}" "${PREFIX}/mime/packages/${MIME_FILE}"

map_size() {
  case "$1" in
    16) echo telegram-multiaccount-sender_16.png ;;
    24) echo telegram-multiaccount-sender_24.png ;;
    32) echo telegram-multiaccount-sender_32.png ;;
    48) echo telegram-multiaccount-sender_48.png ;;
    64) echo telegram-multiaccount-sender_64.png ;;
    128) echo telegram-multiaccount-sender_192.png ;;
    256) echo telegram-multiaccount-sender_256.png ;;
    512) echo telegram-multiaccount-sender_512.png ;;
    *) return 1 ;;
  esac
}

for size in 16 24 32 48 64 128 256 512; do
  src_name="$(map_size "${size}")"
  src="${ICON_SRC}/${src_name}"
  if [[ ! -f "${src}" ]]; then
    continue
  fi
  app_dir="${PREFIX}/icons/hicolor/${size}x${size}/apps"
  mime_dir="${PREFIX}/icons/hicolor/${size}x${size}/mimetypes"
  mkdir -p "${app_dir}" "${mime_dir}"
  install -m 644 "${src}" "${app_dir}/${APP_ID}.png"
  install -m 644 "${src}" "${mime_dir}/application-x-tmas-backup.png"
done

update-desktop-database "${PREFIX}/applications" 2>/dev/null || true
update-mime-database "${PREFIX}/mime" 2>/dev/null || true
if command -v xdg-mime >/dev/null 2>&1; then
  xdg-mime default "${DESKTOP_FILE}" "${MIME_TYPE}" 2>/dev/null || true
fi
if command -v gtk-update-icon-cache >/dev/null 2>&1; then
  gtk-update-icon-cache -f -t "${PREFIX}/icons/hicolor" 2>/dev/null || true
fi

echo "Installed Telegram Multi-Account Message Sender"
echo "  Binary:  ${BIN_DIR}/telegram-multi-account-sender"
echo "  Desktop: ${PREFIX}/applications/${DESKTOP_FILE}"
echo "  MIME:    ${MIME_TYPE} (*.tmas-backup.zip)"
echo
echo "Ensure ${BIN_DIR} is on your PATH, then launch from the app menu or:"
echo "  telegram-multi-account-sender"
echo
echo "Verify file association:"
echo "  xdg-mime query filetype some-backup.tmas-backup.zip"
echo "  # expect: application/x-tmas-backup"
