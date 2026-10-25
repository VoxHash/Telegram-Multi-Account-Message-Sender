"""
Registry plugin: normalize whitespace in outgoing campaign messages.

Installable via the official plugin registry. Uses absolute imports so the
file can live under the user plugins directory (``app_data/plugins``).
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType

_MULTI_SPACE = re.compile(r"[ \t]{2,}")
_MULTI_NEWLINE = re.compile(r"\n{3,}")


class WhitespaceNormalizeFilterPlugin(MessageFilterPlugin):
    """Filter plugin that trims and collapses excess whitespace in messages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Whitespace Normalize Filter",
            version="1.0.0",
            description=(
                "Trims edges and collapses repeated spaces/newlines in outgoing "
                "campaign messages."
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
            tags=["filter", "whitespace", "hygiene", "community", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {
            "trim": True,
            "collapse_spaces": True,
            "collapse_newlines": True,
        }

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        for key in ("trim", "collapse_spaces", "collapse_newlines"):
            if key in config and not isinstance(config[key], bool):
                return False, f"{key} must be a boolean"
        return True, None

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        if not self._enabled:
            return message
        text = message
        if self._config.get("collapse_spaces", True):
            text = _MULTI_SPACE.sub(" ", text)
        if self._config.get("collapse_newlines", True):
            text = _MULTI_NEWLINE.sub("\n\n", text)
        if self._config.get("trim", True):
            text = text.strip()
        return text

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Whitespace Normalize Filter enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Whitespace Normalize Filter disabled")
