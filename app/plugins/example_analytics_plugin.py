"""
Example analytics plugin demonstrating analytics tracking.

This plugin tracks campaign events and logs them.
"""

from typing import Dict, Any, Optional
from datetime import datetime

from ..core.plugin import Plugin, PluginMetadata, PluginType, AnalyticsPlugin


class ExampleAnalyticsPlugin(AnalyticsPlugin):
    """Example plugin that tracks analytics events."""
    
    def __init__(self, api):
        """Initialize plugin."""
        super().__init__(api)
        self.events = []
        self._metadata = PluginMetadata(
            name="Example Analytics Plugin",
            version="1.0.0",
            description="Example plugin that demonstrates analytics tracking",
            author="VoxHash",
            plugin_type=PluginType.ANALYTICS,
            dependencies=[],
            tags=["example", "analytics", "tracking"]
        )
    
    @property
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata."""
        return self._metadata
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration."""
        return {
            "track_campaigns": True,
            "track_messages": True,
            "max_events": 1000
        }
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate configuration."""
        if "max_events" in config:
            if not isinstance(config["max_events"], int) or config["max_events"] < 1:
                return False, "max_events must be a positive integer"
        return True, None
    
    def track_event(self, event_name: str, data: Dict[str, Any]):
        """
        Track an analytics event.
        
        Args:
            event_name: Name of the event
            data: Event data dictionary
        """
        if not self._enabled:
            return
        
        max_events = self._config.get("max_events", 1000)
        
        # Store event
        event = {
            "name": event_name,
            "data": data,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        self.events.append(event)
        
        # Limit events
        if len(self.events) > max_events:
            self.events = self.events[-max_events:]
        
        # Log event
        logger = self.api.get_logger()
        if logger:
            logger.debug(f"Analytics event: {event_name} - {data}")
    
    def on_enable(self):
        """Called when plugin is enabled."""
        logger = self.api.get_logger()
        if logger:
            logger.info("Example Analytics Plugin enabled")
    
    def on_disable(self):
        """Called when plugin is disabled."""
        logger = self.api.get_logger()
        if logger:
            logger.info("Example Analytics Plugin disabled")
    
    def get_events(self) -> list:
        """Get tracked events."""
        return self.events.copy()

