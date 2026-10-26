#!/usr/bin/env bash
# Sign a macOS .app with Developer ID (hardened runtime) and optionally notarize
# via notarytool, then staple. Also supports signing/notarizing a .dmg.
#
# This script never invents credentials. Without the required env vars it exits
# with code 2 and a clear message so CI can skip publishing a signed build.
#
# Required for signing:
#   APPLE_SIGNING_IDENTITY  — e.g. "Developer ID Application: Example Org (TEAMID)"
#
# Required for notarization (App Store Connect API key — preferred):
#   APPLE_API_KEY_PATH      — path to AuthKey_XXXXXX.p8
#     OR APPLE_API_KEY_BASE64 — base64 of the .p8 (decoded to a temp file)
#   APPLE_API_KEY_ID        — Key ID
#   APPLE_API_ISSUER        — Issuer UUID
#
# Alternative notarization (Apple ID + app-specific password):
#   APPLE_ID                — Apple ID email
#   APPLE_APP_PASSWORD      — app-specific password
#   APPLE_TEAM_ID           — 10-character Team ID
#
# Usage:
#   ./sign-and-notarize.sh --self-check
#   ./sign-and-notarize.sh path/to/App.app
#   ./sign-and-notarize.sh path/to/App.app --dmg path/to/App.dmg
#   ./sign-and-notarize.sh path/to/App.app --skip-notarize
#   ./sign-and-notarize.sh path/to/App.dmg --dmg-only
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENTITLEMENTS="${SCRIPT_DIR}/entitlements.plist"
SKIP_NOTARIZE=0
DMG_PATH=""
DMG_ONLY=0
TARGET=""
TMP_FILES=()

cleanup() {
  local f
  for f in "${TMP_FILES[@]:-}"; do
    rm -f "${f}" 2>/dev/null || true
  done
}
trap cleanup EXIT

usage() {
  cat <<'EOF'
Usage: sign-and-notarize.sh [--self-check] <App.app|file.dmg> [--dmg path.dmg] [--skip-notarize] [--dmg-only]

Signs with Developer ID + hardened runtime entitlements, submits to Apple
notarytool, and staples the ticket. Requires macOS and real Apple credentials
in the environment (never committed to this repo).

Env (signing): APPLE_SIGNING_IDENTITY
Env (notarize API key): APPLE_API_KEY_PATH or APPLE_API_KEY_BASE64,
                        APPLE_API_KEY_ID, APPLE_API_ISSUER
Env (notarize Apple ID): APPLE_ID, APPLE_APP_PASSWORD, APPLE_TEAM_ID

Exit codes:
  0  success
  1  usage / host error
  2  missing credentials (safe for CI to treat as "skip signed publish")
EOF
}

self_check() {
  local ok=1
  echo "sign-and-notarize.sh: self-check"
  if [[ ! -f "${ENTITLEMENTS}" ]]; then
    echo "MISSING entitlements.plist at ${ENTITLEMENTS}" >&2
    ok=0
  else
    echo "OK entitlements.plist"
    grep -q "com.apple.security.cs.disable-library-validation" "${ENTITLEMENTS}" \
      || { echo "MISSING disable-library-validation entitlement" >&2; ok=0; }
    grep -q "com.apple.security.cs.allow-jit" "${ENTITLEMENTS}" \
      || { echo "MISSING allow-jit entitlement" >&2; ok=0; }
    grep -q "com.apple.security.network.client" "${ENTITLEMENTS}" \
      || { echo "MISSING network.client entitlement" >&2; ok=0; }
  fi
  if [[ ! -x "${SCRIPT_DIR}/import-identity.sh" ]] && [[ ! -f "${SCRIPT_DIR}/import-identity.sh" ]]; then
    echo "MISSING import-identity.sh" >&2
    ok=0
  else
    echo "OK import-identity.sh"
  fi
  echo "Expected Actions secrets (names only; values never logged):"
  echo "  APPLE_CERTIFICATE_BASE64 APPLE_CERTIFICATE_PASSWORD APPLE_SIGNING_IDENTITY"
  echo "  APPLE_API_KEY_BASE64 APPLE_API_KEY_ID APPLE_API_ISSUER"
  echo "  (alt) APPLE_ID APPLE_APP_PASSWORD APPLE_TEAM_ID"
  if [[ "${ok}" -ne 1 ]]; then
    exit 1
  fi
  echo "self-check passed"
  exit 0
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --self-check)
      self_check
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --skip-notarize)
      SKIP_NOTARIZE=1
      shift
      ;;
    --dmg)
      DMG_PATH="${2:-}"
      shift 2
      ;;
    --dmg-only)
      DMG_ONLY=1
      shift
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
    *)
      if [[ -n "${TARGET}" ]]; then
        echo "Unexpected extra argument: $1" >&2
        exit 1
      fi
      TARGET="$1"
      shift
      ;;
  esac
done

if [[ -z "${TARGET}" ]]; then
  usage >&2
  exit 1
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "sign-and-notarize.sh must run on macOS." >&2
  exit 1
fi

if [[ ! -e "${TARGET}" ]]; then
  echo "Target not found: ${TARGET}" >&2
  exit 1
fi

if [[ -z "${APPLE_SIGNING_IDENTITY:-}" ]]; then
  echo "APPLE_SIGNING_IDENTITY is not set." >&2
  echo "Import a Developer ID cert first (import-identity.sh) or set the identity string." >&2
  exit 2
fi

if [[ ! -f "${ENTITLEMENTS}" ]]; then
  echo "Missing entitlements: ${ENTITLEMENTS}" >&2
  exit 1
fi

sign_file() {
  local path="$1"
  codesign --force --timestamp --options runtime \
    --entitlements "${ENTITLEMENTS}" \
    --sign "${APPLE_SIGNING_IDENTITY}" \
    "${path}"
}

sign_app_bundle() {
  local app="$1"
  echo "Signing nested Mach-O / frameworks inside ${app} (inside-out)..."
  # Sign leaf binaries first (PyInstaller puts helpers under MacOS + Frameworks)
  while IFS= read -r -d '' bin; do
    # Skip the top-level .app itself; sign contents only in this pass
    if [[ "${bin}" == "${app}" ]]; then
      continue
    fi
    if file -b "${bin}" 2>/dev/null | grep -qE 'Mach-O|shared library|bundle'; then
      sign_file "${bin}" || true
    fi
  done < <(find "${app}/Contents" \( -type f -o -type d -name '*.framework' -o -type d -name '*.dylib' \) -print0 2>/dev/null)

  # Explicit passes for common PyInstaller layouts
  if [[ -d "${app}/Contents/Frameworks" ]]; then
    find "${app}/Contents/Frameworks" -type f \( -name '*.dylib' -o -name '*.so' -o -perm -111 \) -print0 \
      | while IFS= read -r -d '' f; do sign_file "${f}"; done
    find "${app}/Contents/Frameworks" -type d -name '*.framework' -print0 \
      | while IFS= read -r -d '' f; do sign_file "${f}"; done
  fi
  if [[ -d "${app}/Contents/MacOS" ]]; then
    find "${app}/Contents/MacOS" -type f -print0 \
      | while IFS= read -r -d '' f; do sign_file "${f}"; done
  fi

  echo "Signing app bundle..."
  sign_file "${app}"
  codesign --verify --deep --strict --verbose=2 "${app}"
  echo "codesign verify OK"
}

resolve_api_key_path() {
  if [[ -n "${APPLE_API_KEY_PATH:-}" && -f "${APPLE_API_KEY_PATH}" ]]; then
    echo "${APPLE_API_KEY_PATH}"
    return 0
  fi
  if [[ -n "${APPLE_API_KEY_BASE64:-}" ]]; then
    local key_file
    key_file="$(mktemp "${TMPDIR:-/tmp}/tmas-notary-key.XXXXXX.p8")"
    TMP_FILES+=("${key_file}")
    echo -n "${APPLE_API_KEY_BASE64}" | base64 --decode > "${key_file}"
    chmod 600 "${key_file}"
    echo "${key_file}"
    return 0
  fi
  return 1
}

notarize_path() {
  local submit_path="$1"
  local zip_path=""
  local to_submit="${submit_path}"

  if [[ -d "${submit_path}" ]]; then
    zip_path="$(mktemp "${TMPDIR:-/tmp}/tmas-notarize.XXXXXX.zip")"
    TMP_FILES+=("${zip_path}")
    ditto -c -k --keepParent "${submit_path}" "${zip_path}"
    to_submit="${zip_path}"
  fi

  echo "Submitting to Apple notary service (notarytool)..."
  local api_key=""
  if api_key="$(resolve_api_key_path)"; then
    if [[ -z "${APPLE_API_KEY_ID:-}" || -z "${APPLE_API_ISSUER:-}" ]]; then
      echo "APPLE_API_KEY_ID and APPLE_API_ISSUER are required with an API key." >&2
      exit 2
    fi
    xcrun notarytool submit "${to_submit}" \
      --key "${api_key}" \
      --key-id "${APPLE_API_KEY_ID}" \
      --issuer "${APPLE_API_ISSUER}" \
      --wait
  elif [[ -n "${APPLE_ID:-}" && -n "${APPLE_APP_PASSWORD:-}" && -n "${APPLE_TEAM_ID:-}" ]]; then
    xcrun notarytool submit "${to_submit}" \
      --apple-id "${APPLE_ID}" \
      --password "${APPLE_APP_PASSWORD}" \
      --team-id "${APPLE_TEAM_ID}" \
      --wait
  else
    echo "Notarization credentials missing." >&2
    echo "Set APPLE_API_KEY_PATH (or APPLE_API_KEY_BASE64) + APPLE_API_KEY_ID + APPLE_API_ISSUER" >&2
    echo "or APPLE_ID + APPLE_APP_PASSWORD + APPLE_TEAM_ID." >&2
    exit 2
  fi

  echo "Stapling notarization ticket..."
  xcrun stapler staple "${submit_path}"
  xcrun stapler validate "${submit_path}" || true
  echo "Notarization + staple complete for ${submit_path}"
}

# --- main ---
if [[ "${DMG_ONLY}" -eq 1 ]]; then
  if [[ "${TARGET}" != *.dmg ]]; then
    echo "--dmg-only expects a .dmg path" >&2
    exit 1
  fi
  sign_file "${TARGET}"
  if [[ "${SKIP_NOTARIZE}" -eq 0 ]]; then
    notarize_path "${TARGET}"
  fi
  exit 0
fi

if [[ "${TARGET}" == *.app || -d "${TARGET}" ]]; then
  sign_app_bundle "${TARGET}"
  if [[ "${SKIP_NOTARIZE}" -eq 0 ]]; then
    notarize_path "${TARGET}"
  fi
elif [[ "${TARGET}" == *.dmg ]]; then
  sign_file "${TARGET}"
  if [[ "${SKIP_NOTARIZE}" -eq 0 ]]; then
    notarize_path "${TARGET}"
  fi
else
  echo "Unsupported target (expected .app or .dmg): ${TARGET}" >&2
  exit 1
fi

if [[ -n "${DMG_PATH}" ]]; then
  if [[ ! -f "${DMG_PATH}" ]]; then
    echo "DMG not found for secondary sign/notarize: ${DMG_PATH}" >&2
    exit 1
  fi
  echo "Signing DMG ${DMG_PATH}..."
  sign_file "${DMG_PATH}"
  if [[ "${SKIP_NOTARIZE}" -eq 0 ]]; then
    notarize_path "${DMG_PATH}"
  fi
fi

echo "Done."
