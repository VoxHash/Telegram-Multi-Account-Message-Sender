#!/usr/bin/env bash
# Import a Developer ID Application certificate (.p12, base64) into a temporary
# keychain for CI or local signing. Never prints certificate/password contents.
#
# Required env:
#   APPLE_CERTIFICATE_BASE64   — base64-encoded .p12 (Developer ID Application)
#   APPLE_CERTIFICATE_PASSWORD — password for the .p12
#
# Optional env:
#   APPLE_KEYCHAIN_PASSWORD    — temp keychain unlock password (default: random)
#   APPLE_KEYCHAIN_PATH        — keychain path (default: $RUNNER_TEMP or /tmp)
#
# Outputs (GitHub Actions compatible):
#   Writes KEYCHAIN_PATH and (if detectable) SIGNING_IDENTITY to GITHUB_OUTPUT
#   when GITHUB_OUTPUT is set. Also exports KEYCHAIN_PATH for the current shell
#   when sourced.
#
# Usage:
#   ./packaging/macos/import-identity.sh
#   source ./packaging/macos/import-identity.sh   # export KEYCHAIN_PATH
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ "${1:-}" == "--self-check" ]]; then
  echo "import-identity.sh: self-check OK"
  echo "Expected secrets (repo Actions secrets; never commit):"
  echo "  APPLE_CERTIFICATE_BASE64"
  echo "  APPLE_CERTIFICATE_PASSWORD"
  echo "Optional: APPLE_KEYCHAIN_PASSWORD, APPLE_KEYCHAIN_PATH"
  exit 0
fi

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "import-identity.sh must run on macOS (security / codesign)." >&2
  exit 1
fi

if [[ -z "${APPLE_CERTIFICATE_BASE64:-}" ]]; then
  echo "APPLE_CERTIFICATE_BASE64 is not set — cannot import a signing identity." >&2
  echo "Add the Developer ID Application .p12 (base64) as a GitHub Actions secret." >&2
  exit 2
fi

if [[ -z "${APPLE_CERTIFICATE_PASSWORD:-}" ]]; then
  echo "APPLE_CERTIFICATE_PASSWORD is not set." >&2
  exit 2
fi

TMP_ROOT="${RUNNER_TEMP:-/tmp}"
KEYCHAIN_PATH="${APPLE_KEYCHAIN_PATH:-${TMP_ROOT}/tmas-signing.keychain-db}"
CERT_PATH="${TMP_ROOT}/tmas-developer-id.p12"
KEYCHAIN_PASSWORD="${APPLE_KEYCHAIN_PASSWORD:-}"

if [[ -z "${KEYCHAIN_PASSWORD}" ]]; then
  KEYCHAIN_PASSWORD="$(openssl rand -base64 32)"
fi

cleanup_partial() {
  rm -f "${CERT_PATH}" 2>/dev/null || true
}
trap cleanup_partial EXIT

echo -n "${APPLE_CERTIFICATE_BASE64}" | base64 --decode > "${CERT_PATH}"
# Refuse empty or tiny payloads (likely misconfigured secret)
CERT_SIZE="$(wc -c < "${CERT_PATH}" | tr -d ' ')"
if [[ "${CERT_SIZE}" -lt 100 ]]; then
  echo "Decoded certificate is too small (${CERT_SIZE} bytes); check APPLE_CERTIFICATE_BASE64." >&2
  exit 2
fi

security delete-keychain "${KEYCHAIN_PATH}" 2>/dev/null || true
security create-keychain -p "${KEYCHAIN_PASSWORD}" "${KEYCHAIN_PATH}"
security set-keychain-settings -lut 21600 "${KEYCHAIN_PATH}"
security unlock-keychain -p "${KEYCHAIN_PASSWORD}" "${KEYCHAIN_PATH}"
security import "${CERT_PATH}" \
  -k "${KEYCHAIN_PATH}" \
  -P "${APPLE_CERTIFICATE_PASSWORD}" \
  -T /usr/bin/codesign \
  -T /usr/bin/security \
  -A
security set-key-partition-list -S apple-tool:,apple: -k "${KEYCHAIN_PASSWORD}" "${KEYCHAIN_PATH}" >/dev/null
security list-keychains -d user -s "${KEYCHAIN_PATH}" login.keychain-db 2>/dev/null \
  || security list-keychains -d user -s "${KEYCHAIN_PATH}" login.keychain

# Prefer an explicit identity; otherwise detect Developer ID Application
SIGNING_IDENTITY="${APPLE_SIGNING_IDENTITY:-}"
if [[ -z "${SIGNING_IDENTITY}" ]]; then
  SIGNING_IDENTITY="$(
    security find-identity -v -p codesigning "${KEYCHAIN_PATH}" 2>/dev/null \
      | sed -n 's/.*"\(Developer ID Application[^"]*\)".*/\1/p' \
      | head -n1
  )"
fi

if [[ -z "${SIGNING_IDENTITY}" ]]; then
  echo "No Developer ID Application identity found in the imported keychain." >&2
  echo "Set APPLE_SIGNING_IDENTITY to the exact codesign identity string." >&2
  exit 2
fi

rm -f "${CERT_PATH}"
trap - EXIT

export KEYCHAIN_PATH
export APPLE_SIGNING_IDENTITY="${SIGNING_IDENTITY}"

if [[ -n "${GITHUB_OUTPUT:-}" ]]; then
  {
    echo "keychain_path=${KEYCHAIN_PATH}"
    echo "signing_identity=${SIGNING_IDENTITY}"
  } >> "${GITHUB_OUTPUT}"
fi

echo "Imported signing identity into temporary keychain (identity name omitted from logs)."
echo "KEYCHAIN_PATH=${KEYCHAIN_PATH}"
# Do not echo the identity string if it embeds personal names in some certs —
# callers already have APPLE_SIGNING_IDENTITY when they set it explicitly.
echo "Signing identity ready for codesign."
