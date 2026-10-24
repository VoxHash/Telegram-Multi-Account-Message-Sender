"""
Registry plugin: strip or replace URLs in outgoing campaign messages.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType

_URL_PATTERN = re.compile(
    r"https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
)


class UrlStripFilterPlugin(MessageFilterPlugin):
    """Filter plugin that removes or replaces HTTP(S) URLs in messages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="URL Strip Filter",
            version="1.0.0",
            description="Removes or replaces HTTP(S) URLs in outgoing campaign messages.",
            author="VoxHash",
            plugin_type=PluginType.FILTER,
            dependencies=[],
            min_app_version="1.2.0",
            homepage="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
            repository=(
                "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
                "/tree/main/registry/plugins"
            ),
            license="EPL-2.0",
            tags=["filter", "url", "compliance", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {"remove_urls": True, "replace_with": "[URL]"}

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if "remove_urls" in config and not isinstance(config["remove_urls"], bool):
            return False, "remove_urls must be a boolean"
        if "replace_with" in config and not isinstance(config["replace_with"], str):
            return False, "replace_with must be a string"
        return True, None

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        if not self._enabled:
            return message
        if not self._config.get("remove_urls", True):
            return message
        replace_with = str(self._config.get("replace_with", "[URL]"))
        return _URL_PATTERN.sub(replace_with, message)

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("URL Strip Filter enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("URL Strip Filter disabled")
