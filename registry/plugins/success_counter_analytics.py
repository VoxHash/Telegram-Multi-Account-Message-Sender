"""
Registry plugin: count message/campaign success events for operators.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.plugin import AnalyticsPlugin, PluginMetadata, PluginType


class SuccessCounterAnalyticsPlugin(AnalyticsPlugin):
    """Analytics plugin that tallies success-like events and mirrors them to the logger."""

    def __init__(self, api: Any) -> None:
        super().__init__(api)
        self.success_count: int = 0
        self.recent_successes: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Success Counter Analytics",
            version="1.0.0",
            description=(
                "Counts message/campaign success events and keeps a short recent "
                "success list for operators."
            ),
            author="VoxHash",
            plugin_type=PluginType.ANALYTICS,
            dependencies=[],
            min_app_version="1.2.0",
            homepage="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
            repository=(
                "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
                "/tree/main/registry/plugins"
            ),
            license="EPL-2.0",
            tags=["analytics", "success", "community", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "max_recent": 100,
            "log_each": True,
            "match_substrings": ["success", "sent", "deliver", "complete"],
        }

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if "max_recent" in config:
            value = config["max_recent"]
            if not isinstance(value, int) or value < 1:
                return False, "max_recent must be a positive integer"
        if "log_each" in config and not isinstance(config["log_each"], bool):
            return False, "log_each must be a boolean"
        if "match_substrings" in config:
            value = config["match_substrings"]
            if not isinstance(value, list) or not all(isinstance(x, str) for x in value):
                return False, "match_substrings must be a list of strings"
        return True, None

    def _is_success_event(self, event_name: str) -> bool:
        lowered = event_name.lower()
        needles = self._config.get(
            "match_substrings",
            ["success", "sent", "deliver", "complete"],
        )
        if not isinstance(needles, list):
            needles = ["success", "sent", "deliver", "complete"]
        return any(str(n).lower() in lowered for n in needles if n)

    def track_event(self, event_name: str, data: Dict[str, Any]) -> None:
        if not self._enabled:
            return
        if not self._is_success_event(event_name):
            return

        self.success_count += 1
        max_recent = int(self._config.get("max_recent", 100))
        entry = {"event": event_name, "data": dict(data), "index": self.success_count}
        self.recent_successes.append(entry)
        if len(self.recent_successes) > max_recent:
            self.recent_successes = self.recent_successes[-max_recent:]

        if self._config.get("log_each", True):
            logger = self.api.get_logger()
            if logger:
                logger.info(
                    f"Success counter ({self.success_count}): {event_name} {data}"
                )

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Success Counter Analytics enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info(
                f"Success Counter Analytics disabled (total successes={self.success_count})"
            )
