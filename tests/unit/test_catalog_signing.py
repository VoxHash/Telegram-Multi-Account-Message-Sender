"""
Unit tests for Ed25519 plugin catalog signing and verification.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.services.catalog_signing import (
    OFFICIAL_KEY_ID,
    CatalogSignatureError,
    canonicalize_catalog_payload,
    generate_ed25519_keypair,
    load_trusted_keys,
    public_key_b64_from_private,
    sign_catalog_payload,
    verify_catalog_payload,
    write_trusted_keys_file,
    _b64encode,
)
from app.services.plugin_registry import PluginRegistryError, parse_catalog
from app.services.plugin_sdk import (
    parse_plugin_catalog_sign_argv,
    run_plugin_catalog_sign_cli,
    validate_catalog_schema,
)


def _sample_catalog() -> dict:
    return {
        "schema_version": 1,
        "name": "Test Registry",
        "updated_at": "2026-10-24",
        "homepage": "https://example.com/registry",
        "plugins": [
            {
                "id": "voxhash.test-filter",
                "name": "Test Filter",
                "version": "1.0.0",
                "description": "Test",
                "author": "VoxHash",
                "plugin_type": "filter",
                "tags": ["filter"],
                "download_url": "https://example.com/p.py",
                "sha256": "a" * 64,
                "filename": "p.py",
                "bundled": False,
                "local_only": False,
            }
        ],
    }


class TestCatalogSigningHelpers:
    def test_canonicalize_strips_signature_and_sorts(self):
        payload = {"b": 1, "a": 2, "signature": {"sig": "x"}}
        canon = canonicalize_catalog_payload(payload)
        assert b"signature" not in canon
        assert canon == b'{"a":2,"b":1}'

    def test_sign_and_verify_roundtrip(self, tmp_path):
        private_key, _, _ = generate_ed25519_keypair()
        pub_b64 = public_key_b64_from_private(private_key)
        keys_path = tmp_path / "trusted_keys.json"
        write_trusted_keys_file(
            keys_path, key_id=OFFICIAL_KEY_ID, public_key_b64=pub_b64
        )
        trusted = load_trusted_keys(keys_path)

        signed = sign_catalog_payload(
            _sample_catalog(), private_key=private_key, key_id=OFFICIAL_KEY_ID
        )
        result = verify_catalog_payload(signed, trusted_keys=trusted, require=True)
        assert result.present is True
        assert result.verified is True
        assert result.key_id == OFFICIAL_KEY_ID

    def test_tampered_catalog_fails(self, tmp_path):
        private_key, _, _ = generate_ed25519_keypair()
        pub_b64 = public_key_b64_from_private(private_key)
        keys_path = tmp_path / "trusted_keys.json"
        write_trusted_keys_file(
            keys_path, key_id=OFFICIAL_KEY_ID, public_key_b64=pub_b64
        )
        trusted = load_trusted_keys(keys_path)
        signed = sign_catalog_payload(
            _sample_catalog(), private_key=private_key, key_id=OFFICIAL_KEY_ID
        )
        signed["name"] = "Tampered"
        with pytest.raises(CatalogSignatureError, match="verification failed"):
            verify_catalog_payload(signed, trusted_keys=trusted, require=True)

    def test_require_signature_rejects_unsigned(self):
        with pytest.raises(CatalogSignatureError, match="required"):
            verify_catalog_payload(_sample_catalog(), require=True)

    def test_parse_catalog_require_signature(self, tmp_path):
        private_key, _, _ = generate_ed25519_keypair()
        pub_b64 = public_key_b64_from_private(private_key)
        # Point bundled trusted keys at a temp file via monkeypatch in verify path:
        # parse_catalog loads bundled keys — write over bundled is heavy; instead
        # sign with official key from repo trusted keys if available, else skip require
        # by injecting via verify only.
        keys_path = tmp_path / "trusted_keys.json"
        write_trusted_keys_file(
            keys_path, key_id="test-key", public_key_b64=pub_b64
        )
        signed = sign_catalog_payload(
            _sample_catalog(), private_key=private_key, key_id="test-key"
        )
        # Direct verify with temp keys
        verify_catalog_payload(
            signed, trusted_keys=load_trusted_keys(keys_path), require=True
        )

        with pytest.raises(PluginRegistryError, match="required|Unknown|verification"):
            parse_catalog(_sample_catalog(), source="test", require_signature=True)

    def test_official_bundled_catalog_verifies(self):
        from app.services.plugin_registry import bundled_catalog_path, load_catalog_from_path

        catalog = load_catalog_from_path(
            bundled_catalog_path(), source="bundled", require_signature=True
        )
        assert catalog.signature_verified is True
        assert catalog.signature_key_id == OFFICIAL_KEY_ID

    def test_validate_schema_warns_when_unsigned(self):
        catalog, report = validate_catalog_schema(_sample_catalog(), source="test")
        assert catalog is not None
        assert any("unsigned" in i.message for i in report.issues)


class TestPluginCatalogSignCli:
    def test_parse_argv(self):
        is_mode, catalog, key, key_id, output, in_place, help_req = (
            parse_plugin_catalog_sign_argv(
                [
                    "telegram-sender",
                    "plugin-catalog-sign",
                    "catalog.json",
                    "--private-key",
                    "k.priv",
                    "--in-place",
                    "--key-id",
                    "my-key",
                ]
            )
        )
        assert is_mode is True
        assert catalog == Path("catalog.json")
        assert key == Path("k.priv")
        assert key_id == "my-key"
        assert in_place is True
        assert output is None
        assert help_req is False

    def test_run_sign_cli_in_place(self, tmp_path):
        private_key, priv_raw, _ = generate_ed25519_keypair()
        pub_b64 = public_key_b64_from_private(private_key)
        # Install temp trusted keys into bundled path? CLI verify uses bundled keys.
        # Sign with a key that matches bundled official key is hard; instead write
        # private key matching a temp trusted keys file and monkeypatch load_trusted_keys.
        from unittest.mock import patch

        from app.services.catalog_signing import TrustedPublicKey

        priv_path = tmp_path / "sign.priv"
        priv_path.write_text(_b64encode(priv_raw) + "\n", encoding="utf-8")
        catalog_path = tmp_path / "catalog.json"
        catalog_path.write_text(json.dumps(_sample_catalog()), encoding="utf-8")

        trusted = [
            TrustedPublicKey(key_id="cli-test-key", public_key_b64=pub_b64)
        ]
        with patch(
            "app.services.catalog_signing.load_trusted_keys",
            return_value=trusted,
        ):
            code = run_plugin_catalog_sign_cli(
                [
                    "telegram-sender",
                    "plugin-catalog-sign",
                    str(catalog_path),
                    "--private-key",
                    str(priv_path),
                    "--key-id",
                    "cli-test-key",
                    "--in-place",
                ]
            )
        assert code == 0
        signed = json.loads(catalog_path.read_text(encoding="utf-8"))
        assert "signature" in signed
        assert signed["signature"]["key_id"] == "cli-test-key"
