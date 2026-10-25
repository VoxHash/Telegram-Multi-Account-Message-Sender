"""
Unit tests for further community registry volume plugins (v1.2.36).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.services.plugin_sdk import compute_file_sha256, validate_plugin_file

REPO_ROOT = Path(__file__).resolve().parents[2]
OFFICIAL_PLUGINS = REPO_ROOT / "registry" / "plugins"
OFFICIAL_CATALOG = REPO_ROOT / "registry" / "catalog.json"
BUNDLED_CATALOG = REPO_ROOT / "app" / "plugins" / "registry" / "catalog.json"
EMOJI = OFFICIAL_PLUGINS / "emoji_strip_filter.py"
SUCCESS = OFFICIAL_PLUGINS / "success_counter_analytics.py"


class _FakeApi:
    def __init__(self) -> None:
        self.messages: List[str] = []

    def get_logger(self) -> "_FakeApi":
        return self

    def info(self, msg: str) -> None:
        self.messages.append(f"info:{msg}")

    def warning(self, msg: str) -> None:
        self.messages.append(f"warning:{msg}")


def _load_plugin_class(path: Path):
    import importlib.util
    import inspect

    from app.core.plugin import Plugin

    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in dir(module):
        obj = getattr(module, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, Plugin)
            and obj is not Plugin
            and not inspect.isabstract(obj)
            and getattr(obj, "__module__", None) == module.__name__
        ):
            return obj
    raise AssertionError(f"no plugin class in {path}")


class TestEmojiStripFilter:
    def test_validate_ok(self):
        assert validate_plugin_file(EMOJI).ok

    def test_strips_emoji_and_collapses_spaces(self):
        cls = _load_plugin_class(EMOJI)
        plugin = cls(_FakeApi())
        plugin.set_config(plugin.get_default_config())
        plugin.enable()
        out = plugin.filter_message("Hello 😀 world 🚀!", {})
        assert "😀" not in out
        assert "🚀" not in out
        assert "Hello" in out
        assert "world" in out

    def test_disabled_passthrough(self):
        cls = _load_plugin_class(EMOJI)
        plugin = cls(_FakeApi())
        plugin.set_config(plugin.get_default_config())
        # not enabled
        assert plugin.filter_message("Hi 😀", {}) == "Hi 😀"

    def test_validate_config_rejects_bad_types(self):
        cls = _load_plugin_class(EMOJI)
        plugin = cls(_FakeApi())
        ok, err = plugin.validate_config({"strip_emoji": "yes"})
        assert ok is False
        assert err is not None


class TestSuccessCounterAnalytics:
    def test_validate_ok(self):
        assert validate_plugin_file(SUCCESS).ok

    def test_counts_success_events(self):
        cls = _load_plugin_class(SUCCESS)
        plugin = cls(_FakeApi())
        plugin.set_config(plugin.get_default_config())
        plugin.enable()
        plugin.track_event("message_sent", {"recipient": "x"})
        plugin.track_event("campaign_complete", {"id": 1})
        plugin.track_event("message_failed", {"recipient": "y"})
        assert plugin.success_count == 2
        assert len(plugin.recent_successes) == 2

    def test_respects_max_recent(self):
        cls = _load_plugin_class(SUCCESS)
        plugin = cls(_FakeApi())
        plugin.set_config({"max_recent": 2, "log_each": False})
        plugin.enable()
        for i in range(5):
            plugin.track_event("sent", {"i": i})
        assert plugin.success_count == 5
        assert len(plugin.recent_successes) == 2
        assert plugin.recent_successes[-1]["data"]["i"] == 4

    def test_validate_config_rejects_bad_max(self):
        cls = _load_plugin_class(SUCCESS)
        plugin = cls(_FakeApi())
        ok, err = plugin.validate_config({"max_recent": 0})
        assert ok is False
        assert err is not None


class TestOfficialCatalogVolume:
    def test_volume_plugins_present_and_hashed(self):
        payload = json.loads(OFFICIAL_CATALOG.read_text(encoding="utf-8"))
        by_id = {p["id"]: p for p in payload["plugins"]}
        assert "voxhash.emoji-strip-filter" in by_id
        assert "voxhash.success-counter-analytics" in by_id
        assert by_id["voxhash.emoji-strip-filter"]["sha256"] == compute_file_sha256(EMOJI)
        assert by_id["voxhash.success-counter-analytics"]["sha256"] == compute_file_sha256(
            SUCCESS
        )
        assert "community" in by_id["voxhash.emoji-strip-filter"]["tags"]
        assert "community" in by_id["voxhash.success-counter-analytics"]["tags"]
        # six installable (non-local) entries: 2 official + 4 community
        installable = [
            p
            for p in payload["plugins"]
            if not p.get("local_only") and not p.get("bundled")
        ]
        assert len(installable) == 6
        assert "signature" in payload

    def test_bundled_catalog_matches_official(self):
        official = OFFICIAL_CATALOG.read_text(encoding="utf-8")
        bundled = BUNDLED_CATALOG.read_text(encoding="utf-8")
        assert official == bundled
