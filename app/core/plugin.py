"""
Plugin system base classes and interfaces for Telegram Multi-Account Message Sender.

This module provides the foundation for a plugin architecture that allows
third-party extensions to enhance the application's functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
import importlib
import inspect
from pathlib import Path


class PluginStatus(str, Enum):
    """Plugin status enumeration."""
    LOADED = "loaded"
    ENABLED = "enabled"
    DISABLED = "disabled"
    ERROR = "error"
    UNLOADED = "unloaded"


class PluginType(str, Enum):
    """Plugin type enumeration."""
    ANALYTICS = "analytics"
    FILTER = "filter"
    TRANSFORMER = "transformer"
    NOTIFICATION = "notification"
    INTEGRATION = "integration"
    UI_EXTENSION = "ui_extension"
    CUSTOM = "custom"


@dataclass
class PluginMetadata:
    """Plugin metadata information."""
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    dependencies: List[str] = field(default_factory=list)
    min_app_version: Optional[str] = None
    max_app_version: Optional[str] = None
    homepage: Optional[str] = None
    repository: Optional[str] = None
    license: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class PluginInfo:
    """Complete plugin information."""
    metadata: PluginMetadata
    status: PluginStatus
    path: Optional[str] = None
    error_message: Optional[str] = None
    loaded_at: Optional[datetime] = None
    enabled_at: Optional[datetime] = None
    config: Dict[str, Any] = field(default_factory=dict)


class PluginAPI:
    """
    Plugin API interface providing access to application services.
    
    Plugins use this API to interact with the application without
    directly accessing internal components.
    """
    
    def __init__(self, services: Dict[str, Any]):
        """
        Initialize Plugin API with application services.
        
        Args:
            services: Dictionary of available services (logger, settings, db, etc.)
        """
        self.services = services
        self._hooks: Dict[str, List[Callable]] = {}
    
    def get_logger(self):
        """Get application logger."""
        return self.services.get('logger')
    
    def get_settings(self):
        """Get application settings."""
        return self.services.get('settings')
    
    def get_session(self):
        """Get database session."""
        return self.services.get('session')()
    
    def get_campaign_manager(self):
        """Get campaign manager service."""
        return self.services.get('campaign_manager')
    
    def register_hook(self, hook_name: str, callback: Callable):
        """
        Register a hook callback.
        
        Args:
            hook_name: Name of the hook (e.g., 'before_send_message', 'after_campaign_start')
            callback: Callback function to execute
        """
        if hook_name not in self._hooks:
            self._hooks[hook_name] = []
        self._hooks[hook_name].append(callback)
    
    def unregister_hook(self, hook_name: str, callback: Callable):
        """Unregister a hook callback."""
        if hook_name in self._hooks:
            if callback in self._hooks[hook_name]:
                self._hooks[hook_name].remove(callback)
    
    def call_hook(self, hook_name: str, *args, **kwargs) -> List[Any]:
        """
        Call all registered hooks for a given hook name.
        
        Args:
            hook_name: Name of the hook to call
            *args: Positional arguments to pass to hooks
            **kwargs: Keyword arguments to pass to hooks
            
        Returns:
            List of return values from all hook callbacks
        """
        results = []
        if hook_name in self._hooks:
            for callback in self._hooks[hook_name]:
                try:
                    result = callback(*args, **kwargs)
                    results.append(result)
                except Exception as e:
                    logger = self.get_logger()
                    if logger:
                        logger.error(f"Error in hook {hook_name}: {e}")
        return results


class Plugin(ABC):
    """
    Base class for all plugins.
    
    Plugins must inherit from this class and implement required methods.
    """
    
    def __init__(self, api: PluginAPI):
        """
        Initialize plugin with API access.
        
        Args:
            api: PluginAPI instance for accessing application services
        """
        self.api = api
        self._enabled = False
        self._config: Dict[str, Any] = {}
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Get plugin metadata. Must be implemented by subclasses."""
        pass
    
    @property
    def is_enabled(self) -> bool:
        """Check if plugin is enabled."""
        return self._enabled
    
    @property
    def config(self) -> Dict[str, Any]:
        """Get plugin configuration."""
        return self._config
    
    def set_config(self, config: Dict[str, Any]):
        """Set plugin configuration."""
        self._config = config
    
    def enable(self):
        """Enable the plugin. Called when plugin is enabled."""
        if not self._enabled:
            self._enabled = True
            self.on_enable()
    
    def disable(self):
        """Disable the plugin. Called when plugin is disabled."""
        if self._enabled:
            self._enabled = False
            self.on_disable()
    
    def on_enable(self):
        """Called when plugin is enabled. Override in subclasses."""
        pass
    
    def on_disable(self):
        """Called when plugin is disabled. Override in subclasses."""
        pass
    
    def on_load(self):
        """Called when plugin is loaded. Override in subclasses."""
        pass
    
    def on_unload(self):
        """Called when plugin is unloaded. Override in subclasses."""
        pass
    
    def validate_config(self, config: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate plugin configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        return True, None
    
    def get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for the plugin."""
        return {}


class MessageFilterPlugin(Plugin):
    """Base class for message filtering plugins."""
    
    @abstractmethod
    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        """
        Filter or transform a message before sending.
        
        Args:
            message: Original message text
            recipient: Recipient information dictionary
            
        Returns:
            Filtered/transformed message, or None to skip sending
        """
        pass


class AnalyticsPlugin(Plugin):
    """Base class for analytics plugins."""
    
    @abstractmethod
    def track_event(self, event_name: str, data: Dict[str, Any]):
        """
        Track an analytics event.
        
        Args:
            event_name: Name of the event
            data: Event data dictionary
        """
        pass


class NotificationPlugin(Plugin):
    """Base class for notification plugins."""
    
    @abstractmethod
    def send_notification(self, title: str, message: str, level: str = "info"):
        """
        Send a notification.
        
        Args:
            title: Notification title
            message: Notification message
            level: Notification level (info, warning, error, success)
        """
        pass


class IntegrationPlugin(Plugin):
    """Base class for integration plugins."""
    
    @abstractmethod
    def connect(self) -> bool:
        """Connect to external service. Returns True if successful."""
        pass
    
    @abstractmethod
    def disconnect(self):
        """Disconnect from external service."""
        pass
    
    @property
    @abstractmethod
    def is_connected(self) -> bool:
        """Check if connected to external service."""
        pass

