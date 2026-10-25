"""Regression checks for the blocking mypy scope (v1.2.40+)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List
from unittest.mock import MagicMock

import pytest

from app.core.plugin import PluginAPI
from app.plugins.example_analytics_plugin import ExampleAnalyticsPlugin
from app.plugins.example_filter_plugin import ExampleFilterPlugin

REPO_ROOT = Path(__file__).resolve().parents[2]

# Keep in sync with [tool.mypy] files= and CI "Type check with mypy".
BLOCKING_MYPY_PATHS = [
    "app/core",
    "app/services",
    "app/models",
    "app/plugins",
    "app/gui/__init__.py",
    "app/gui/theme.py",
    "app/gui/widgets/__init__.py",
    "app/gui/widgets/about_widget.py",
    "app/gui/widgets/plugin_widget.py",
    "app/gui/widgets/testing_widget.py",
    "app/gui/widgets/telegram_selector.py",
]


@pytest.mark.unit
def test_blocking_mypy_paths_exist() -> None:
    """Every path under the blocking mypy gate must exist in the tree."""
    for rel in BLOCKING_MYPY_PATHS:
        path = REPO_ROOT / rel
        assert path.exists(), f"missing blocking mypy path: {rel}"


@pytest.mark.unit
def test_example_filter_plugin_lifecycle_annotations() -> None:
    """Example filter plugin enable/disable and filter path stay typed and usable."""
    api = MagicMock(spec=PluginAPI)
    logger = MagicMock()
    api.get_logger.return_value = logger
    plugin = ExampleFilterPlugin(api)
    plugin.set_config(plugin.get_default_config())
    plugin._enabled = True

    plugin.on_enable()
    logger.info.assert_called()
    filtered = plugin.filter_message("see https://example.com now", {"id": "1"})
    assert filtered is not None
    assert "https://example.com" not in filtered
    plugin.on_disable()
    logger.info.assert_called()


@pytest.mark.unit
def test_example_analytics_plugin_events_typed() -> None:
    """Example analytics plugin tracks events with a typed event list."""
    api = MagicMock(spec=PluginAPI)
    api.get_logger.return_value = MagicMock()
    plugin = ExampleAnalyticsPlugin(api)
    plugin.set_config(plugin.get_default_config())
    plugin._enabled = True

    plugin.track_event("campaign_start", {"campaign_id": 42})
    events: List[Dict[str, Any]] = plugin.get_events()
    assert len(events) == 1
    assert events[0]["name"] == "campaign_start"
    assert events[0]["data"]["campaign_id"] == 42
    assert isinstance(events[0]["timestamp"], str)
