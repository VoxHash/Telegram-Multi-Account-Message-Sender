"""
Registry plugin: strip emoji and pictographs from outgoing campaign messages.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType

# Targeted Unicode emoji / pictograph ranges (no third-party dependency).
_EMOJI_PATTERN = re.compile(
    "["
    "\U0001F300-\U0001F5FF"  # Misc Symbols and Pictographs
    "\U0001F600-\U0001F64F"  # Emoticons
    "\U0001F680-\U0001F6FF"  # Transport and Map
    "\U0001F1E0-\U0001F1FF"  # Regional Indicator Symbols (flags)
    "\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    "\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    "\U00002600-\U000026FF"  # Misc symbols (sun, etc.)
    "\U00002702-\U000027B0"  # Dingbats
    "\U0000FE0E-\U0000FE0F"  # Variation selectors
    "\U0000200D"  # Zero Width Joiner (emoji sequences)
    "]+",
    flags=re.UNICODE,
)
_MULTI_SPACE = re.compile(r"[ \t]{2,}")


class EmojiStripFilterPlugin(MessageFilterPlugin):
    """Filter plugin that removes emoji/pictographs from messages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Emoji Strip Filter",
            version="1.0.0",
            description=(
                "Removes emoji and pictograph characters from outgoing campaign "
                "messages (optional space tidy)."
            ),
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
            tags=["filter", "emoji", "hygiene", "compliance", "community", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "strip_emoji": True,
            "collapse_spaces": True,
            "trim": True,
            "replace_with": "",
        }

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        for key in ("strip_emoji", "collapse_spaces", "trim"):
            if key in config and not isinstance(config[key], bool):
                return False, f"{key} must be a boolean"
        if "replace_with" in config and not isinstance(config["replace_with"], str):
            return False, "replace_with must be a string"
        return True, None

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        if not self._enabled:
            return message
        if not self._config.get("strip_emoji", True):
            return message
        replace_with = str(self._config.get("replace_with", ""))
        text = _EMOJI_PATTERN.sub(replace_with, message)
        if self._config.get("collapse_spaces", True):
            text = _MULTI_SPACE.sub(" ", text)
        if self._config.get("trim", True):
            text = text.strip()
        return text

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Emoji Strip Filter enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Emoji Strip Filter disabled")
