"""
Registry plugin: count message/campaign failure events for operators.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.plugin import AnalyticsPlugin, PluginMetadata, PluginType


class FailureCounterAnalyticsPlugin(AnalyticsPlugin):
    """Analytics plugin that tallies failure-like events and mirrors them to the logger."""

    def __init__(self, api: Any) -> None:
        super().__init__(api)
        self.failure_count: int = 0
        self.recent_failures: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Failure Counter Analytics",
            version="1.0.0",
            description=(
                "Counts message/campaign failure events and keeps a short recent "
                "failure list for operators."
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
            tags=["analytics", "failures", "community", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "max_recent": 100,
            "log_each": True,
            "match_substrings": ["fail", "error", "reject", "banned"],
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

    def _is_failure_event(self, event_name: str) -> bool:
        lowered = event_name.lower()
        needles = self._config.get(
            "match_substrings",
            ["fail", "error", "reject", "banned"],
        )
        if not isinstance(needles, list):
            needles = ["fail", "error", "reject", "banned"]
        return any(str(n).lower() in lowered for n in needles if n)

    def track_event(self, event_name: str, data: Dict[str, Any]) -> None:
        if not self._enabled:
            return
        if not self._is_failure_event(event_name):
            return

        self.failure_count += 1
        max_recent = int(self._config.get("max_recent", 100))
        entry = {"event": event_name, "data": dict(data), "index": self.failure_count}
        self.recent_failures.append(entry)
        if len(self.recent_failures) > max_recent:
            self.recent_failures = self.recent_failures[-max_recent:]

        if self._config.get("log_each", True):
            logger = self.api.get_logger()
            if logger:
                logger.warning(
                    f"Failure counter ({self.failure_count}): {event_name} {data}"
                )

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Failure Counter Analytics enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info(
                f"Failure Counter Analytics disabled (total failures={self.failure_count})"
            )
