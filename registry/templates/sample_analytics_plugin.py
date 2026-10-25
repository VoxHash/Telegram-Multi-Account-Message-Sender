"""
Sample registry plugin template (analytics).

Copy this file, rename it, then:

1. Change the class name and ``PluginMetadata`` fields.
2. Implement ``track_event`` (or switch base class for filter / etc.).
3. Use **absolute** imports only (``from app.core.plugin import …``) so the
   file works under ``app_data/plugins/`` after registry install.
4. Generate a catalog entry::

       telegram-sender plugin-catalog-entry path/to/your_plugin.py

5. Validate before opening a PR::

       telegram-sender plugin-validate path/to/your_plugin.py
       telegram-sender plugin-validate registry/catalog.json \\
           --plugins-dir registry/plugins
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.plugin import AnalyticsPlugin, PluginMetadata, PluginType


class SampleAnalyticsPlugin(AnalyticsPlugin):
    """Template analytics plugin: stores recent events in memory."""

    def __init__(self, api: Any) -> None:
        super().__init__(api)
        self.events: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Sample Analytics Plugin",
            version="1.0.0",
            description="Template analytics plugin for registry submissions.",
            author="Your Name",
            plugin_type=PluginType.ANALYTICS,
            dependencies=[],
            min_app_version="1.2.0",
            homepage="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
            repository=(
                "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
                "/tree/main/registry/templates"
            ),
            license="EPL-2.0",
            tags=["example", "analytics", "template", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {"max_events": 500, "log_each": False}

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if "max_events" in config:
            value = config["max_events"]
            if not isinstance(value, int) or value < 1:
                return False, "max_events must be a positive integer"
        if "log_each" in config and not isinstance(config["log_each"], bool):
            return False, "log_each must be a boolean"
        return True, None

    def track_event(self, event_name: str, data: Dict[str, Any]) -> None:
        if not self._enabled:
            return
        max_events = int(self._config.get("max_events", 500))
        self.events.append({"event": event_name, "data": dict(data)})
        if len(self.events) > max_events:
            self.events = self.events[-max_events:]
        if self._config.get("log_each", False):
            logger = self.api.get_logger()
            if logger:
                logger.info(f"Sample analytics: {event_name} {data}")

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Sample Analytics Plugin enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Sample Analytics Plugin disabled")
