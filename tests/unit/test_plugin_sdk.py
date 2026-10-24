"""
Unit tests for plugin / registry developer SDK validation helpers and CLI.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Dict

import pytest

from app.services.plugin_sdk import (
    SUPPORTED_CATALOG_SCHEMA_VERSION,
    check_min_app_version,
    compare_versions,
    compute_file_sha256,
    format_validation_report,
    parse_plugin_validate_argv,
    parse_version_tuple,
    run_plugin_validate_cli,
    validate_catalog_file,
    validate_catalog_schema,
    validate_catalog_sha256,
    validate_plugin_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_CATALOG = REPO_ROOT / "registry" / "catalog.json"
OFFICIAL_PLUGINS = REPO_ROOT / "registry" / "plugins"
SAMPLE_TEMPLATE = REPO_ROOT / "registry" / "templates" / "sample_filter_plugin.py"
URL_STRIP = OFFICIAL_PLUGINS / "url_strip_filter.py"


def _minimal_catalog(plugin: Dict[str, Any] | None = None) -> Dict[str, Any]:
    entry = plugin or {
        "id": "voxhash.sdk-test",
        "name": "SDK Test",
        "version": "1.0.0",
        "description": "Test entry",
        "author": "VoxHash",
        "plugin_type": "filter",
        "tags": ["test"],
        "download_url": "https://example.com/plugins/sdk_test.py",
        "sha256": "a" * 64,
        "filename": "sdk_test.py",
        "bundled": False,
        "local_only": False,
        "min_app_version": "1.2.0",
    }
    return {
        "schema_version": SUPPORTED_CATALOG_SCHEMA_VERSION,
        "name": "SDK Test Registry",
        "updated_at": "2026-10-24",
        "homepage": "https://example.com",
        "plugins": [entry],
    }


class TestVersionHelpers:
    def test_parse_and_compare(self):
        assert parse_version_tuple("1.2.30") == (1, 2, 30)
        assert compare_versions("1.2.29", "1.2.30") == -1
        assert compare_versions("1.2.30", "1.2.30") == 0
        assert compare_versions("2.0.0", "1.9.9") == 1

    def test_parse_invalid(self):
        with pytest.raises(ValueError):
            parse_version_tuple("not-a-version")

    def test_min_app_version_check(self):
        assert check_min_app_version("1.2.0", "1.2.30") is None
        msg = check_min_app_version("9.0.0", "1.2.30")
        assert msg is not None
        assert "below" in msg
        assert check_min_app_version(None, "1.2.30") is None


class TestCatalogValidation:
    def test_official_catalog_ok(self):
        catalog, report = validate_catalog_file(OFFICIAL_CATALOG, app_version="1.2.30")
        assert catalog is not None
        assert report.ok, format_validation_report(report)
        assert catalog.schema_version == SUPPORTED_CATALOG_SCHEMA_VERSION

    def test_official_sha256_matches_plugins(self):
        catalog, report = validate_catalog_file(OFFICIAL_CATALOG)
        assert catalog is not None
        assert report.ok
        sha_report = validate_catalog_sha256(catalog, OFFICIAL_PLUGINS)
        assert sha_report.ok, format_validation_report(sha_report)

    def test_future_schema_version_errors(self):
        payload = _minimal_catalog()
        payload["schema_version"] = SUPPORTED_CATALOG_SCHEMA_VERSION + 1
        catalog, report = validate_catalog_schema(payload, source="test")
        assert catalog is not None
        assert not report.ok
        assert any("newer than supported" in i.message for i in report.issues)

    def test_sha256_mismatch(self, tmp_path: Path):
        plugin_bytes = b'print("hello")\n'
        digest = hashlib.sha256(plugin_bytes).hexdigest()
        wrong = "b" * 64
        payload = _minimal_catalog(
            {
                "id": "voxhash.sdk-test",
                "name": "SDK Test",
                "version": "1.0.0",
                "description": "Test entry",
                "author": "VoxHash",
                "plugin_type": "filter",
                "tags": [],
                "download_url": "https://example.com/p.py",
                "sha256": wrong,
                "filename": "sdk_test.py",
            }
        )
        (tmp_path / "sdk_test.py").write_bytes(plugin_bytes)
        catalog, report = validate_catalog_schema(payload, source="mem")
        assert catalog is not None
        assert report.ok or any(i.level == "warning" for i in report.issues)
        sha_report = validate_catalog_sha256(catalog, tmp_path)
        assert not sha_report.ok
        assert any("SHA-256 mismatch" in i.message for i in sha_report.issues)
        # Correct digest passes
        payload["plugins"][0]["sha256"] = digest
        catalog2, _ = validate_catalog_schema(payload, source="mem")
        assert catalog2 is not None
        assert validate_catalog_sha256(catalog2, tmp_path).ok

    def test_compute_file_sha256(self, tmp_path: Path):
        path = tmp_path / "x.py"
        data = b"abc"
        path.write_bytes(data)
        assert compute_file_sha256(path) == hashlib.sha256(data).hexdigest()


class TestPluginFileValidation:
    def test_official_url_strip_ok(self):
        report = validate_plugin_file(URL_STRIP, app_version="1.2.30")
        assert report.ok, format_validation_report(report)

    def test_sample_template_ok(self):
        assert SAMPLE_TEMPLATE.is_file()
        report = validate_plugin_file(SAMPLE_TEMPLATE, app_version="1.2.30")
        assert report.ok, format_validation_report(report)

    def test_relative_import_rejected(self, tmp_path: Path):
        bad = tmp_path / "bad_plugin.py"
        bad.write_text(
            """
from ..core.plugin import MessageFilterPlugin, PluginMetadata, PluginType

class BadPlugin(MessageFilterPlugin):
    @property
    def metadata(self):
        return PluginMetadata(
            name="Bad",
            version="1.0.0",
            description="bad",
            author="x",
            plugin_type=PluginType.FILTER,
        )
    def filter_message(self, message, recipient):
        return message
""",
            encoding="utf-8",
        )
        report = validate_plugin_file(bad)
        assert not report.ok
        assert any("relative import" in i.message for i in report.issues)

    def test_missing_plugin_subclass(self, tmp_path: Path):
        empty = tmp_path / "noop.py"
        empty.write_text("VALUE = 1\n", encoding="utf-8")
        report = validate_plugin_file(empty)
        assert not report.ok
        assert any("no concrete Plugin subclass" in i.message for i in report.issues)


class TestPluginValidateCli:
    def test_parse_argv(self):
        is_m, target, plugins_dir, app_ver, help_req = parse_plugin_validate_argv(
            [
                "telegram-sender",
                "plugin-validate",
                "catalog.json",
                "--plugins-dir",
                "plugins",
                "--app-version",
                "1.2.30",
            ]
        )
        assert is_m is True
        assert target == Path("catalog.json")
        assert plugins_dir == Path("plugins")
        assert app_ver == "1.2.30"
        assert help_req is False

    def test_parse_non_mode(self):
        is_m, *_ = parse_plugin_validate_argv(["telegram-sender", "web-monitor"])
        assert is_m is False

    def test_parse_help(self):
        is_m, _, _, _, help_req = parse_plugin_validate_argv(
            ["telegram-sender", "plugin-validate", "--help"]
        )
        assert is_m is True
        assert help_req is True

    def test_run_validate_official_catalog(self, capsys):
        code = run_plugin_validate_cli(
            [
                "telegram-sender",
                "plugin-validate",
                str(OFFICIAL_CATALOG),
                "--plugins-dir",
                str(OFFICIAL_PLUGINS),
                "--app-version",
                "1.2.30",
            ]
        )
        captured = capsys.readouterr()
        assert code == 0
        assert "OK" in captured.out

    def test_run_validate_sample_plugin(self, capsys):
        code = run_plugin_validate_cli(
            [
                "telegram-sender",
                "plugin-validate",
                str(SAMPLE_TEMPLATE),
                "--app-version",
                "1.2.30",
            ]
        )
        assert code == 0
        assert "OK" in capsys.readouterr().out

    def test_run_help(self, capsys):
        code = run_plugin_validate_cli(["telegram-sender", "plugin-validate", "--help"])
        assert code == 0
        assert "Usage:" in capsys.readouterr().out
