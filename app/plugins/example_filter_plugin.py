"""
Example message filter plugin demonstrating the plugin system.

This plugin filters messages by removing URLs or replacing them with placeholders.
"""

from typing import Optional, Dict, Any
import re

from ..core.plugin import PluginMetadata, PluginType, MessageFilterPlugin


class ExampleFilterPlugin(MessageFilterPlugin):
    """Example plugin that filters messages by removing URLs."""

    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return PluginMetadata(
            name="Example Filter Plugin",
            version="1.0.0",
            description="Example plugin that demonstrates message filtering by removing URLs",
            author="VoxHash",
            plugin_type=PluginType.FILTER,
            dependencies=[],
            tags=["example", "filter", "url"],
        )

    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {"remove_urls": True, "replace_with": "[URL]"}

    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration."""
        if "remove_urls" in config and not isinstance(config["remove_urls"], bool):
            return False, "remove_urls must be a boolean"
        if "replace_with" in config and not isinstance(config["replace_with"], str):
            return False, "replace_with must be a string"
        return True, None

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        """
        Filter message by removing or replacing URLs.

        Args:
            message: Original message text
            recipient: Recipient information

        Returns:
            Filtered message or None to skip sending
        """
        if not self._enabled:
            return message

        remove_urls = self._config.get("remove_urls", True)
        replace_with = self._config.get("replace_with", "[URL]")

        if remove_urls:
            # URL pattern
            url_pattern = (
                r"http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+"
            )
            filtered_message = re.sub(url_pattern, replace_with, message)
            return filtered_message

        return message

    def on_enable(self):
        """Called when plugin is enabled."""
        logger = self.api.get_logger()
        if logger:
            logger.info("Example Filter Plugin enabled")

    def on_disable(self):
        """Called when plugin is disabled."""
        logger = self.api.get_logger()
        if logger:
            logger.info("Example Filter Plugin disabled")
