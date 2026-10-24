"""
Unit tests for the official plugin marketplace / registry client.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.services.plugin_registry import (
    DEFAULT_REGISTRY_URL,
    PluginRegistryError,
    PluginRegistryInstallError,
    PluginRegistryOfflineError,
    PluginRegistryService,
    bundled_catalog_path,
    load_catalog_from_path,
    parse_catalog,
    search_catalog,
)


class _FakeHTTPResponse:
    def __init__(self, payload: bytes, status: int = 200) -> None:
        self._raw = payload
        self.status = status

    def read(self, n: int = -1) -> bytes:
        if n is None or n < 0:
            return self._raw
        return self._raw[:n]

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def _sample_catalog_dict() -> Dict[str, Any]:
    plugin_bytes = b'print("hello from registry plugin")\n'
    digest = hashlib.sha256(plugin_bytes).hexdigest()
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
                "description": "Test installable filter plugin",
                "author": "VoxHash",
                "plugin_type": "filter",
                "tags": ["filter", "test"],
                "download_url": "https://example.com/plugins/test_filter.py",
                "sha256": digest,
                "filename": "test_filter.py",
                "bundled": False,
                "local_only": False,
            },
            {
                "id": "voxhash.bundled-example",
                "name": "Bundled Example",
                "version": "1.0.0",
                "description": "Documentation-only bundled entry",
                "author": "VoxHash",
                "plugin_type": "analytics",
                "tags": ["example", "bundled"],
                "download_url": "",
                "sha256": "",
                "filename": "example.py",
                "bundled": True,
                "local_only": True,
            },
        ],
    }, plugin_bytes, digest


class TestCatalogParsing:
    def test_bundled_catalog_loads_and_validates(self):
        path = bundled_catalog_path()
        assert path.is_file()
        catalog = load_catalog_from_path(path, source="bundled")
        assert catalog.schema_version == 1
        assert catalog.source == "bundled"
        assert len(catalog.plugins) >= 2
        ids = {p.id for p in catalog.plugins}
        assert "voxhash.url-strip-filter" in ids
        assert "voxhash.event-logger-analytics" in ids

    def test_parse_rejects_http_download_url(self):
        payload, _, _ = _sample_catalog_dict()
        payload["plugins"][0]["download_url"] = "http://example.com/plugins/test_filter.py"
        with pytest.raises(PluginRegistryError, match="https"):
            parse_catalog(payload, source="path")

    def test_parse_rejects_duplicate_ids(self):
        payload, _, _ = _sample_catalog_dict()
        payload["plugins"].append(dict(payload["plugins"][0]))
        with pytest.raises(PluginRegistryError, match="Duplicate"):
            parse_catalog(payload, source="path")

    def test_search_filters_by_query_and_type(self):
        payload, _, _ = _sample_catalog_dict()
        catalog = parse_catalog(payload, source="path")
        assert len(search_catalog(catalog, query="filter")) == 1
        assert len(search_catalog(catalog, plugin_type="analytics")) == 1
        assert len(search_catalog(catalog, tags=["bundled"])) == 1
        assert search_catalog(catalog, query="no-such-plugin") == []


class TestPluginRegistryService:
    def test_offline_falls_back_to_bundled(self, tmp_path: Path):
        urlopen = MagicMock()
        service = PluginRegistryService(
            registry_url=DEFAULT_REGISTRY_URL,
            install_dir=tmp_path / "plugins",
            urlopen=urlopen,
            network_check=lambda: False,
        )
        catalog = service.fetch_catalog(prefer_remote=True)
        assert catalog.source == "bundled"
        urlopen.assert_not_called()

    def test_remote_catalog_preferred_when_online(self, tmp_path: Path):
        payload, _, _ = _sample_catalog_dict()
        raw = json.dumps(payload).encode("utf-8")

        def fake_urlopen(request: Any, timeout: float = 30.0) -> _FakeHTTPResponse:
            assert request.full_url == "https://example.com/catalog.json"
            return _FakeHTTPResponse(raw)

        service = PluginRegistryService(
            registry_url="https://example.com/catalog.json",
            install_dir=tmp_path / "plugins",
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        catalog = service.fetch_catalog(prefer_remote=True)
        assert catalog.source == "remote"
        assert catalog.name == "Test Registry"
        assert len(catalog.plugins) == 2

    def test_install_verifies_sha256_and_writes_file(self, tmp_path: Path):
        payload, plugin_bytes, digest = _sample_catalog_dict()
        catalog_raw = json.dumps(payload).encode("utf-8")
        calls: list[str] = []

        def fake_urlopen(request: Any, timeout: float = 30.0) -> _FakeHTTPResponse:
            calls.append(request.full_url)
            if request.full_url.endswith("catalog.json"):
                return _FakeHTTPResponse(catalog_raw)
            return _FakeHTTPResponse(plugin_bytes)

        install_dir = tmp_path / "plugins"
        service = PluginRegistryService(
            registry_url="https://example.com/catalog.json",
            install_dir=install_dir,
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        target = service.install("voxhash.test-filter")
        assert target == install_dir / "test_filter.py"
        assert target.read_bytes() == plugin_bytes
        assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
        assert service.is_installed(service.get_entry("voxhash.test-filter"))

    def test_install_rejects_sha_mismatch(self, tmp_path: Path):
        payload, plugin_bytes, _ = _sample_catalog_dict()
        payload["plugins"][0]["sha256"] = "0" * 64
        catalog_raw = json.dumps(payload).encode("utf-8")

        def fake_urlopen(request: Any, timeout: float = 30.0) -> _FakeHTTPResponse:
            if request.full_url.endswith("catalog.json"):
                return _FakeHTTPResponse(catalog_raw)
            return _FakeHTTPResponse(plugin_bytes)

        service = PluginRegistryService(
            registry_url="https://example.com/catalog.json",
            install_dir=tmp_path / "plugins",
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        with pytest.raises(PluginRegistryInstallError, match="SHA-256"):
            service.install("voxhash.test-filter")

    def test_install_local_only_rejected(self, tmp_path: Path):
        payload, _, _ = _sample_catalog_dict()
        catalog_raw = json.dumps(payload).encode("utf-8")

        def fake_urlopen(request: Any, timeout: float = 30.0) -> _FakeHTTPResponse:
            return _FakeHTTPResponse(catalog_raw)

        service = PluginRegistryService(
            registry_url="https://example.com/catalog.json",
            install_dir=tmp_path / "plugins",
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        with pytest.raises(PluginRegistryInstallError, match="documentation-only"):
            service.install("voxhash.bundled-example")

    def test_install_offline_raises(self, tmp_path: Path):
        # Prefetch bundled so get_entry works offline via prefer_remote fallback,
        # then force offline on the download step by installing an installable id
        # from a remote catalog cached after a first online fetch.
        payload, plugin_bytes, _ = _sample_catalog_dict()
        catalog_raw = json.dumps(payload).encode("utf-8")
        online = {"value": True}

        def fake_urlopen(request: Any, timeout: float = 30.0) -> _FakeHTTPResponse:
            if not online["value"]:
                raise OSError("network down")
            if request.full_url.endswith("catalog.json"):
                return _FakeHTTPResponse(catalog_raw)
            return _FakeHTTPResponse(plugin_bytes)

        service = PluginRegistryService(
            registry_url="https://example.com/catalog.json",
            install_dir=tmp_path / "plugins",
            urlopen=fake_urlopen,
            network_check=lambda: online["value"],
        )
        service.fetch_catalog(prefer_remote=True)
        online["value"] = False
        with pytest.raises(PluginRegistryOfflineError):
            service.install("voxhash.test-filter")

    def test_settings_default_registry_url(self):
        from app.services.settings import Settings

        settings = Settings()
        assert "registry/catalog.json" in settings.plugin_registry_url
        assert settings.plugin_registry_url.startswith("https://")
