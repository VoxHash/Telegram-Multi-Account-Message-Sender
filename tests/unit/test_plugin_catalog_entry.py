"""
Unit tests for plugin-catalog-entry builder and CLI (community registry submissions).
"""

from __future__ import annotations

import json
from pathlib import Path

from app.services.plugin_sdk import (
    append_catalog_entry,
    build_catalog_entry_dict,
    compute_file_sha256,
    parse_plugin_catalog_entry_argv,
    run_plugin_catalog_entry_cli,
    slugify_plugin_id_part,
    suggest_catalog_plugin_id,
    validate_plugin_file,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_PLUGINS = REPO_ROOT / "registry" / "plugins"
WHITESPACE = OFFICIAL_PLUGINS / "whitespace_normalize_filter.py"
FAILURE = OFFICIAL_PLUGINS / "failure_counter_analytics.py"
SAMPLE_ANALYTICS = REPO_ROOT / "registry" / "templates" / "sample_analytics_plugin.py"
OFFICIAL_CATALOG = REPO_ROOT / "registry" / "catalog.json"


class TestSlugAndId:
    def test_slugify(self):
        assert slugify_plugin_id_part("Whitespace Normalize Filter") == (
            "whitespace-normalize-filter"
        )
        assert suggest_catalog_plugin_id("VoxHash", "Failure Counter Analytics") == (
            "voxhash.failure-counter-analytics"
        )


class TestBuildCatalogEntry:
    def test_whitespace_plugin_entry(self):
        entry = build_catalog_entry_dict(
            WHITESPACE, plugin_id="voxhash.whitespace-normalize-filter"
        )
        assert entry["id"] == "voxhash.whitespace-normalize-filter"
        assert entry["plugin_type"] == "filter"
        assert entry["filename"] == "whitespace_normalize_filter.py"
        assert entry["sha256"] == compute_file_sha256(WHITESPACE)
        assert entry["download_url"].endswith("/whitespace_normalize_filter.py")
        assert "community" in entry["tags"]

    def test_failure_counter_entry(self):
        entry = build_catalog_entry_dict(FAILURE)
        assert entry["plugin_type"] == "analytics"
        assert entry["sha256"] == compute_file_sha256(FAILURE)
        assert entry["id"].startswith("voxhash.")

    def test_sample_analytics_template_ok(self):
        report = validate_plugin_file(SAMPLE_ANALYTICS)
        assert report.ok
        entry = build_catalog_entry_dict(SAMPLE_ANALYTICS, plugin_id="example.sample-analytics")
        assert entry["plugin_type"] == "analytics"
        assert entry["id"] == "example.sample-analytics"


class TestAppendCatalogEntry:
    def test_append_and_replace(self, tmp_path: Path):
        catalog = {
            "schema_version": 1,
            "name": "Test",
            "updated_at": "2026-10-24",
            "homepage": "https://example.com",
            "plugins": [],
            "signature": {"alg": "ed25519", "sig": "x"},
        }
        path = tmp_path / "catalog.json"
        path.write_text(json.dumps(catalog), encoding="utf-8")
        entry = build_catalog_entry_dict(
            WHITESPACE, plugin_id="voxhash.whitespace-normalize-filter"
        )
        append_catalog_entry(path, entry)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert "signature" not in payload
        assert len(payload["plugins"]) == 1
        assert payload["plugins"][0]["id"] == "voxhash.whitespace-normalize-filter"

        entry["version"] = "1.0.1"
        append_catalog_entry(path, entry, replace_existing=True)
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["plugins"][0]["version"] == "1.0.1"


class TestOfficialCatalogHasCommunityPlugins:
    def test_community_plugins_present_and_hashed(self):
        payload = json.loads(OFFICIAL_CATALOG.read_text(encoding="utf-8"))
        ids = {p["id"] for p in payload["plugins"]}
        assert "voxhash.whitespace-normalize-filter" in ids
        assert "voxhash.failure-counter-analytics" in ids
        assert "voxhash.emoji-strip-filter" in ids
        assert "voxhash.success-counter-analytics" in ids
        by_id = {p["id"]: p for p in payload["plugins"]}
        assert by_id["voxhash.whitespace-normalize-filter"]["sha256"] == compute_file_sha256(
            WHITESPACE
        )
        assert by_id["voxhash.failure-counter-analytics"]["sha256"] == compute_file_sha256(
            FAILURE
        )


class TestCatalogEntryCli:
    def test_parse_argv(self):
        is_mode, path, plugin_id, url, append_to, replace, help_requested = (
            parse_plugin_catalog_entry_argv(
                [
                    "telegram-sender",
                    "plugin-catalog-entry",
                    "plugin.py",
                    "--id",
                    "community.demo",
                    "--download-url",
                    "https://example.com/p.py",
                    "--append-to",
                    "catalog.json",
                    "--replace",
                ]
            )
        )
        assert is_mode is True
        assert path == Path("plugin.py")
        assert plugin_id == "community.demo"
        assert url == "https://example.com/p.py"
        assert append_to == Path("catalog.json")
        assert replace is True
        assert help_requested is False

    def test_run_prints_json(self, capsys):
        code = run_plugin_catalog_entry_cli(
            [
                "telegram-sender",
                "plugin-catalog-entry",
                str(WHITESPACE),
                "--id",
                "voxhash.whitespace-normalize-filter",
            ]
        )
        assert code == 0
        out = capsys.readouterr().out
        entry = json.loads(out)
        assert entry["filename"] == "whitespace_normalize_filter.py"

    def test_run_help(self, capsys):
        code = run_plugin_catalog_entry_cli(
            ["telegram-sender", "plugin-catalog-entry", "--help"]
        )
        assert code == 0
        assert "plugin-catalog-entry" in capsys.readouterr().out
