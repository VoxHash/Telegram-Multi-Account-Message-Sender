"""
Registry plugin: log campaign analytics events to the application logger.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.core.plugin import AnalyticsPlugin, PluginMetadata, PluginType


class EventLoggerAnalyticsPlugin(AnalyticsPlugin):
    """Analytics plugin that records recent events and mirrors them to the logger."""

    def __init__(self, api: Any) -> None:
        super().__init__(api)
        self.events: List[Dict[str, Any]] = []

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Event Logger Analytics",
            version="1.0.0",
            description="Tracks campaign/message events and writes them to the app logger.",
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
            tags=["analytics", "logging", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "track_campaigns": True,
            "track_messages": True,
            "max_events": 1000,
        }

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if "track_campaigns" in config and not isinstance(config["track_campaigns"], bool):
            return False, "track_campaigns must be a boolean"
        if "track_messages" in config and not isinstance(config["track_messages"], bool):
            return False, "track_messages must be a boolean"
        if "max_events" in config:
            value = config["max_events"]
            if not isinstance(value, int) or value < 1:
                return False, "max_events must be a positive integer"
        return True, None

    def track_event(self, event_name: str, data: Dict[str, Any]) -> None:
        if not self._enabled:
            return

        track_campaigns = bool(self._config.get("track_campaigns", True))
        track_messages = bool(self._config.get("track_messages", True))
        max_events = int(self._config.get("max_events", 1000))

        if event_name.startswith("campaign") and not track_campaigns:
            return
        if event_name.startswith("message") and not track_messages:
            return

        entry = {"event": event_name, "data": dict(data)}
        self.events.append(entry)
        if len(self.events) > max_events:
            self.events = self.events[-max_events:]

        logger = self.api.get_logger()
        if logger:
            logger.info(f"Analytics event: {event_name} {data}")

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Event Logger Analytics enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Event Logger Analytics disabled")
