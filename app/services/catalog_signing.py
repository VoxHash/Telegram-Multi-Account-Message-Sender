"""
Ed25519 signatures for plugin registry catalogs.

Canonicalization: ``json-sorted-compact`` — recursively sorted object keys,
compact separators, UTF-8 (Python ``json.dumps(..., sort_keys=True,
separators=(",", ":"))``). The detached ``signature`` object is excluded from
the signed payload (DF-VERIFY-style).
"""

from __future__ import annotations

import base64
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)
from cryptography.hazmat.primitives.serialization import (
    Encoding,
    NoEncryption,
    PrivateFormat,
    PublicFormat,
)

SIGNATURE_ALG = "ed25519"
CANONICALIZATION = "json-sorted-compact"
OFFICIAL_KEY_ID = "voxhash-registry-2026"


class CatalogSignatureError(Exception):
    """Raised when catalog signature creation or verification fails."""


@dataclass(frozen=True)
class TrustedPublicKey:
    """One trusted Ed25519 public key for catalog verification."""

    key_id: str
    public_key_b64: str
    alg: str = SIGNATURE_ALG

    def public_key(self) -> Ed25519PublicKey:
        raw = _b64decode(self.public_key_b64)
        if len(raw) != 32:
            raise CatalogSignatureError(
                f"Public key for {self.key_id} must be 32 raw bytes (got {len(raw)})"
            )
        return Ed25519PublicKey.from_public_bytes(raw)


@dataclass(frozen=True)
class CatalogSignatureInfo:
    """Parsed catalog signature metadata (without crypto verification)."""

    alg: str
    key_id: str
    canonicalization: str
    sig_b64: str


@dataclass(frozen=True)
class CatalogSignatureResult:
    """Outcome of verifying a catalog payload."""

    present: bool
    verified: bool
    key_id: Optional[str] = None
    detail: str = ""


def bundled_trusted_keys_path() -> Path:
    """Path to the offline trusted-keys file shipped with the package."""
    return (
        Path(__file__).resolve().parent.parent
        / "plugins"
        / "registry"
        / "trusted_keys.json"
    )


def repo_trusted_keys_path() -> Path:
    """Path to the source-of-truth trusted keys under ``registry/keys/``."""
    return (
        Path(__file__).resolve().parent.parent.parent
        / "registry"
        / "keys"
        / "trusted_keys.json"
    )


def canonicalize_catalog_payload(payload: Mapping[str, Any]) -> bytes:
    """
    Return canonical UTF-8 bytes for signing/verification.

    Strips a top-level ``signature`` field when present.
    """
    body = {k: v for k, v in payload.items() if k != "signature"}
    text = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return text.encode("utf-8")


def extract_signature(payload: Mapping[str, Any]) -> Optional[CatalogSignatureInfo]:
    """Parse the optional top-level ``signature`` object; return None if absent."""
    raw = payload.get("signature")
    if raw is None:
        return None
    if not isinstance(raw, dict):
        raise CatalogSignatureError("signature must be a JSON object")
    alg = raw.get("alg")
    key_id = raw.get("key_id")
    canon = raw.get("canonicalization")
    sig = raw.get("sig")
    if not isinstance(alg, str) or not alg.strip():
        raise CatalogSignatureError("signature.alg is required")
    if not isinstance(key_id, str) or not key_id.strip():
        raise CatalogSignatureError("signature.key_id is required")
    if not isinstance(canon, str) or not canon.strip():
        raise CatalogSignatureError("signature.canonicalization is required")
    if not isinstance(sig, str) or not sig.strip():
        raise CatalogSignatureError("signature.sig is required")
    return CatalogSignatureInfo(
        alg=alg.strip().lower(),
        key_id=key_id.strip(),
        canonicalization=canon.strip(),
        sig_b64=sig.strip(),
    )


def load_trusted_keys(path: Optional[Path] = None) -> List[TrustedPublicKey]:
    """Load trusted public keys from JSON (bundled path when ``path`` is None)."""
    keys_path = path or bundled_trusted_keys_path()
    try:
        payload = json.loads(keys_path.read_text(encoding="utf-8"))
    except OSError as exc:
        raise CatalogSignatureError(f"Could not read trusted keys: {keys_path}") from exc
    except json.JSONDecodeError as exc:
        raise CatalogSignatureError(f"Invalid trusted keys JSON: {exc}") from exc

    if not isinstance(payload, dict):
        raise CatalogSignatureError("trusted_keys root must be an object")
    raw_keys = payload.get("keys")
    if not isinstance(raw_keys, list) or not raw_keys:
        raise CatalogSignatureError("trusted_keys.keys must be a non-empty list")

    keys: List[TrustedPublicKey] = []
    for index, entry in enumerate(raw_keys):
        if not isinstance(entry, dict):
            raise CatalogSignatureError(f"trusted_keys.keys[{index}] must be an object")
        key_id = entry.get("key_id")
        public_key_b64 = entry.get("public_key_b64")
        alg = (entry.get("alg") or SIGNATURE_ALG).strip().lower()
        if not isinstance(key_id, str) or not key_id.strip():
            raise CatalogSignatureError(f"trusted_keys.keys[{index}].key_id is required")
        if not isinstance(public_key_b64, str) or not public_key_b64.strip():
            raise CatalogSignatureError(
                f"trusted_keys.keys[{index}].public_key_b64 is required"
            )
        if alg != SIGNATURE_ALG:
            raise CatalogSignatureError(
                f"Unsupported trusted key alg for {key_id}: {alg}"
            )
        keys.append(
            TrustedPublicKey(
                key_id=key_id.strip(),
                public_key_b64=public_key_b64.strip(),
                alg=alg,
            )
        )
    return keys


def find_trusted_key(
    keys: Sequence[TrustedPublicKey], key_id: str
) -> Optional[TrustedPublicKey]:
    """Return the trusted key matching ``key_id``, if any."""
    for key in keys:
        if key.key_id == key_id:
            return key
    return None


def verify_catalog_payload(
    payload: Mapping[str, Any],
    *,
    trusted_keys: Optional[Sequence[TrustedPublicKey]] = None,
    require: bool = False,
) -> CatalogSignatureResult:
    """
    Verify an optional catalog ``signature`` against trusted public keys.

    - No signature + ``require=False`` → present=False, verified=False (ok)
    - No signature + ``require=True`` → raises ``CatalogSignatureError``
    - Invalid / unknown key → raises ``CatalogSignatureError``
    """
    info = extract_signature(payload)
    if info is None:
        if require:
            raise CatalogSignatureError(
                "Catalog signature is required but missing "
                "(set PLUGIN_REGISTRY_REQUIRE_SIGNATURE=false to allow unsigned catalogs)"
            )
        return CatalogSignatureResult(
            present=False, verified=False, detail="unsigned catalog"
        )

    if info.alg != SIGNATURE_ALG:
        raise CatalogSignatureError(f"Unsupported signature.alg: {info.alg}")
    if info.canonicalization != CANONICALIZATION:
        raise CatalogSignatureError(
            f"Unsupported signature.canonicalization: {info.canonicalization}"
        )

    keys = list(trusted_keys) if trusted_keys is not None else load_trusted_keys()
    trusted = find_trusted_key(keys, info.key_id)
    if trusted is None:
        raise CatalogSignatureError(f"Unknown signature.key_id: {info.key_id}")

    message = canonicalize_catalog_payload(payload)
    signature = _b64decode(info.sig_b64)
    try:
        trusted.public_key().verify(signature, message)
    except InvalidSignature as exc:
        raise CatalogSignatureError(
            f"Catalog signature verification failed for key_id={info.key_id}"
        ) from exc

    return CatalogSignatureResult(
        present=True,
        verified=True,
        key_id=info.key_id,
        detail=f"verified with {info.key_id}",
    )


def sign_catalog_payload(
    payload: Mapping[str, Any],
    *,
    private_key: Ed25519PrivateKey,
    key_id: str = OFFICIAL_KEY_ID,
) -> Dict[str, Any]:
    """
    Return a new catalog dict with a fresh ``signature`` block.

    Does not mutate ``payload``.
    """
    body = {k: v for k, v in payload.items() if k != "signature"}
    message = canonicalize_catalog_payload(body)
    sig = private_key.sign(message)
    signed = dict(body)
    signed["signature"] = {
        "alg": SIGNATURE_ALG,
        "key_id": key_id,
        "canonicalization": CANONICALIZATION,
        "sig": _b64encode(sig),
    }
    return signed


def generate_ed25519_keypair() -> Tuple[Ed25519PrivateKey, bytes, bytes]:
    """
    Generate a new Ed25519 keypair.

    Returns ``(private_key, raw_private_32, raw_public_32)``.
    """
    private_key = Ed25519PrivateKey.generate()
    private_raw = private_key.private_bytes(
        Encoding.Raw, PrivateFormat.Raw, NoEncryption()
    )
    public_raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return private_key, private_raw, public_raw


def load_private_key_raw_b64(value: str) -> Ed25519PrivateKey:
    """Load an Ed25519 private key from base64-encoded raw 32 bytes."""
    raw = _b64decode(value.strip())
    if len(raw) != 32:
        raise CatalogSignatureError(
            f"Private key must be 32 raw bytes (got {len(raw)})"
        )
    return Ed25519PrivateKey.from_private_bytes(raw)


def load_private_key_file(path: Path) -> Ed25519PrivateKey:
    """
    Load a private key from a file.

    Accepts PEM (``-----BEGIN PRIVATE KEY-----``) or a single-line base64 raw key.
    """
    text = path.read_text(encoding="utf-8").strip()
    if "BEGIN PRIVATE KEY" in text or "BEGIN OPENSSH PRIVATE KEY" in text:
        try:
            loaded = __import__(
                "cryptography.hazmat.primitives.serialization", fromlist=["load_pem_private_key"]
            ).load_pem_private_key(text.encode("utf-8"), password=None)
        except Exception as exc:  # noqa: BLE001
            raise CatalogSignatureError(f"Could not load PEM private key: {exc}") from exc
        if not isinstance(loaded, Ed25519PrivateKey):
            raise CatalogSignatureError("PEM file is not an Ed25519 private key")
        return loaded
    return load_private_key_raw_b64(text)


def public_key_b64_from_private(private_key: Ed25519PrivateKey) -> str:
    """Return URL-safe-tolerant standard base64 of the raw 32-byte public key."""
    raw = private_key.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw)
    return _b64encode(raw)


def write_trusted_keys_file(
    path: Path, *, key_id: str, public_key_b64: str
) -> None:
    """Write a minimal trusted_keys.json for one official key."""
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": 1,
        "keys": [
            {
                "key_id": key_id,
                "alg": SIGNATURE_ALG,
                "public_key_b64": public_key_b64,
            }
        ],
    }
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )


def _b64encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("ascii").rstrip("=")


def _b64decode(value: str) -> bytes:
    text = value.strip()
    pad = "=" * (-len(text) % 4)
    try:
        return base64.urlsafe_b64decode(text + pad)
    except Exception:
        try:
            return base64.b64decode(text + pad)
        except Exception as exc:  # noqa: BLE001
            raise CatalogSignatureError("Invalid base64 in key or signature") from exc
