#!/usr/bin/env bash
# Build the TMMS Rust native accelerator and install the binary under bin/.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRATE="${ROOT}/native/tmms_native"
OUT_DIR="${ROOT}/bin"
BIN_NAME="tmms_native"

if ! command -v cargo >/dev/null 2>&1; then
  echo "cargo not found. Install Rust from https://rustup.rs/ then re-run." >&2
  exit 1
fi

mkdir -p "${OUT_DIR}"
cargo build --release --manifest-path "${CRATE}/Cargo.toml"

SRC="${CRATE}/target/release/${BIN_NAME}"
if [[ ! -x "${SRC}" ]]; then
  # Windows / MSVC layout
  if [[ -x "${CRATE}/target/release/${BIN_NAME}.exe" ]]; then
    SRC="${CRATE}/target/release/${BIN_NAME}.exe"
    BIN_NAME="${BIN_NAME}.exe"
  else
    echo "Release binary missing at ${SRC}" >&2
    exit 1
  fi
fi

install -m 755 "${SRC}" "${OUT_DIR}/${BIN_NAME}"
echo "Installed ${OUT_DIR}/${BIN_NAME}"
"${OUT_DIR}/${BIN_NAME}" <<'EOF'
{"op":"ping"}
EOF
