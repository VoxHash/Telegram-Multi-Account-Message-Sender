"""
Sample registry plugin template (message filter).

Copy this file, rename it, then:

1. Change the class name and ``PluginMetadata`` fields.
2. Implement ``filter_message`` (or switch base class for analytics / etc.).
3. Use **absolute** imports only (``from app.core.plugin import …``) so the
   file works under ``app_data/plugins/`` after registry install.
4. Generate a catalog entry (SHA-256 + metadata)::

       telegram-sender plugin-catalog-entry path/to/your_plugin.py

5. Validate before opening a PR::

       telegram-sender plugin-validate path/to/your_plugin.py
       telegram-sender plugin-validate registry/catalog.json \\
           --plugins-dir registry/plugins
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType


class SampleFilterPlugin(MessageFilterPlugin):
    """Template filter: optionally prefix outgoing campaign messages."""

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="Sample Filter Plugin",
            version="1.0.0",
            description="Template filter plugin for registry submissions.",
            author="Your Name",
            plugin_type=PluginType.FILTER,
            dependencies=[],
            min_app_version="1.2.0",
            homepage="https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender",
            repository=(
                "https://github.com/VoxHash/Telegram-Multi-Account-Message-Sender"
                "/tree/main/registry/templates"
            ),
            license="EPL-2.0",
            tags=["example", "filter", "template", "registry"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        return {"prefix": "", "enabled_prefix": False}

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        if "prefix" in config and not isinstance(config["prefix"], str):
            return False, "prefix must be a string"
        if "enabled_prefix" in config and not isinstance(config["enabled_prefix"], bool):
            return False, "enabled_prefix must be a boolean"
        return True, None

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        if not self._enabled:
            return message
        if not self._config.get("enabled_prefix", False):
            return message
        prefix = str(self._config.get("prefix", ""))
        return f"{prefix}{message}" if prefix else message

    def on_enable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Sample Filter Plugin enabled")

    def on_disable(self) -> None:
        logger = self.api.get_logger()
        if logger:
            logger.info("Sample Filter Plugin disabled")
