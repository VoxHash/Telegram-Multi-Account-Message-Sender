#!/usr/bin/env bash
# Install desktop entry, icons, and .tmas-backup.zip MIME association for the
# current user (XDG paths under ~/.local). No root required.
#
# Modes:
#   default       Install frozen Linux binary from this directory (or dist/) plus desktop/MIME/icons
#   --from-path   Desktop/MIME/icons only; Exec points at an existing CLI (uv tool / pip) on PATH
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PREFIX="${XDG_DATA_HOME:-$HOME/.local/share}"
BIN_DIR="${TMMS_BIN_DIR:-$HOME/.local/bin}"
APP_ID="dev.voxhash.telegram-multi-account-sender"
MIME_TYPE="application/x-tmas-backup"
DESKTOP_FILE="${APP_ID}.desktop"
MIME_FILE="application-x-tmas-backup.xml"
FROM_PATH=0
REMOVE_BINARY_ON_UNINSTALL=1
EXEC_NAME="telegram-multi-account-sender"

usage() {
  cat <<'EOF'
Usage: ./install.sh [--prefix DIR] [--bin-dir DIR] [--from-path] [--uninstall]

Installs Telegram Multi-Account Message Sender into the user XDG layout:
  ~/.local/bin/telegram-multi-account-sender   (default mode only)
  ~/.local/share/applications/<app>.desktop
  ~/.local/share/mime/packages/application-x-tmas-backup.xml
  ~/.local/share/icons/hicolor/*/apps|mimetypes/...

Options:
  --prefix DIR    XDG data home (default: $XDG_DATA_HOME or ~/.local/share)
  --bin-dir DIR   Binary install / lookup directory (default: ~/.local/bin)
  --from-path     Register desktop/MIME/icons only; use an existing install from
                  uv tool / pip (prefers telegram-multi-account-sender-gui).
                  Does not copy or overwrite a binary.
  --uninstall     Remove installed files and refresh desktop/MIME databases
EOF
}

resolve_icon_src() {
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
}

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

install_icons_and_mime() {
  local DESKTOP_SRC MIME_SRC size src_name src app_dir mime_dir
  DESKTOP_SRC="${SCRIPT_DIR}/${DESKTOP_FILE}"
  MIME_SRC="${SCRIPT_DIR}/${MIME_FILE}"
  if [[ ! -f "${DESKTOP_SRC}" || ! -f "${MIME_SRC}" ]]; then
    echo "error: desktop/MIME templates missing beside install.sh" >&2
    exit 1
  fi

  mkdir -p "${PREFIX}/applications" "${PREFIX}/mime/packages"

  # Rewrite Exec/TryExec to the resolved launcher so menus work without PATH hacks.
  local tmp_desktop
  tmp_desktop="$(mktemp)"
  sed \
    -e "s|^Exec=.*|Exec=${EXEC_PATH} %f|" \
    -e "/^TryExec=/d" \
    "${DESKTOP_SRC}" > "${tmp_desktop}"
  # Insert TryExec after Exec
  awk -v tryexec="TryExec=${EXEC_PATH}" '
    { print }
    /^Exec=/ && !done { print tryexec; done=1 }
  ' "${tmp_desktop}" > "${tmp_desktop}.out"
  install -m 644 "${tmp_desktop}.out" "${PREFIX}/applications/${DESKTOP_FILE}"
  rm -f "${tmp_desktop}" "${tmp_desktop}.out"

  install -m 644 "${MIME_SRC}" "${PREFIX}/mime/packages/${MIME_FILE}"

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

  if [[ -f "${ICON_SRC}/telegram-multiaccount-sender.svg" ]]; then
    mkdir -p "${PREFIX}/icons/hicolor/scalable/apps"
    install -m 644 "${ICON_SRC}/telegram-multiaccount-sender.svg" \
      "${PREFIX}/icons/hicolor/scalable/apps/${APP_ID}.svg"
  fi
}

refresh_desktop_databases() {
  update-desktop-database "${PREFIX}/applications" 2>/dev/null || true
  update-mime-database "${PREFIX}/mime" 2>/dev/null || true
  if command -v xdg-mime >/dev/null 2>&1; then
    xdg-mime default "${DESKTOP_FILE}" "${MIME_TYPE}" 2>/dev/null || true
  fi
  if command -v gtk-update-icon-cache >/dev/null 2>&1; then
    gtk-update-icon-cache -f -t "${PREFIX}/icons/hicolor" 2>/dev/null || true
  fi
  if command -v kbuildsycoca6 >/dev/null 2>&1; then
    kbuildsycoca6 --noincremental 2>/dev/null || true
  elif command -v kbuildsycoca5 >/dev/null 2>&1; then
    kbuildsycoca5 --noincremental 2>/dev/null || true
  fi
}

uninstall() {
  if [[ "${REMOVE_BINARY_ON_UNINSTALL}" -eq 1 ]]; then
    rm -f "${BIN_DIR}/telegram-multi-account-sender"
  fi
  rm -f "${PREFIX}/applications/${DESKTOP_FILE}"
  rm -f "${PREFIX}/mime/packages/${MIME_FILE}"
  for size in 16 24 32 48 64 128 256 512; do
    rm -f "${PREFIX}/icons/hicolor/${size}x${size}/apps/${APP_ID}.png"
    rm -f "${PREFIX}/icons/hicolor/${size}x${size}/mimetypes/application-x-tmas-backup.png"
  done
  rm -f "${PREFIX}/icons/hicolor/scalable/apps/${APP_ID}.svg"
  update-desktop-database "${PREFIX}/applications" 2>/dev/null || true
  update-mime-database "${PREFIX}/mime" 2>/dev/null || true
  echo "Uninstalled ${APP_ID} from ${PREFIX}"
  if [[ "${REMOVE_BINARY_ON_UNINSTALL}" -eq 1 ]]; then
    echo "  (also removed ${BIN_DIR}/telegram-multi-account-sender if present)"
  else
    echo "  (left PATH/uv-tool binaries untouched; use: uv tool uninstall telegram-multi-account-sender)"
  fi
}

resolve_from_path_exec() {
  local candidate
  for candidate in \
    "${BIN_DIR}/telegram-multi-account-sender-gui" \
    "${BIN_DIR}/telegram-sender-gui" \
    "${BIN_DIR}/telegram-multi-account-sender" \
    "${BIN_DIR}/telegram-sender"
  do
    if [[ -x "${candidate}" ]]; then
      EXEC_PATH="${candidate}"
      return 0
    fi
  done
  for candidate in \
    telegram-multi-account-sender-gui \
    telegram-sender-gui \
    telegram-multi-account-sender \
    telegram-sender
  do
    if command -v "${candidate}" >/dev/null 2>&1; then
      EXEC_PATH="$(command -v "${candidate}")"
      return 0
    fi
  done
  echo "error: no telegram-multi-account-sender CLI found on PATH or in ${BIN_DIR}" >&2
  echo "Install first, e.g.:" >&2
  echo "  uv tool install git+https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender.git@v1.2.51" >&2
  exit 1
}

DO_UNINSTALL=0
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
    --from-path)
      FROM_PATH=1
      REMOVE_BINARY_ON_UNINSTALL=0
      shift
      ;;
    --uninstall)
      DO_UNINSTALL=1
      shift
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

if [[ "${DO_UNINSTALL}" -eq 1 ]]; then
  uninstall
  exit 0
fi

resolve_icon_src

if [[ "${FROM_PATH}" -eq 1 ]]; then
  resolve_from_path_exec
  install_icons_and_mime
  refresh_desktop_databases
  echo "Registered Telegram Multi-Account Message Sender (from existing PATH install)"
  echo "  Exec:    ${EXEC_PATH}"
  echo "  Desktop: ${PREFIX}/applications/${DESKTOP_FILE}"
  echo "  MIME:    ${MIME_TYPE} (*.tmas-backup.zip)"
  echo
  echo "Add to Favorites (KDE / Glytherra Studio launcher):"
  echo "  Application Launcher → All Applications → search \"Telegram Multi-Account\""
  echo "  → right-click → Add to Favorites (or pin / Add to Panel)."
  exit 0
fi

BINARY="${SCRIPT_DIR}/telegram-multi-account-sender"
if [[ ! -f "${BINARY}" ]]; then
  # Allow running from the repo packaging/linux tree against dist/
  if [[ -f "${SCRIPT_DIR}/../../dist/telegram-multi-account-sender" ]]; then
    BINARY="${SCRIPT_DIR}/../../dist/telegram-multi-account-sender"
  else
    echo "error: binary not found next to install.sh (expected telegram-multi-account-sender)" >&2
    echo "Assemble a release dir with packaging/linux/assemble-dist.sh first," >&2
    echo "or use --from-path after: uv tool install ... / pip install ..." >&2
    exit 1
  fi
fi

mkdir -p "${BIN_DIR}"
install -m 755 "${BINARY}" "${BIN_DIR}/telegram-multi-account-sender"
EXEC_PATH="${BIN_DIR}/telegram-multi-account-sender"

install_icons_and_mime
refresh_desktop_databases

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
