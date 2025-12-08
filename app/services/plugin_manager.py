"""
Plugin manager service for loading, managing, and executing plugins.
"""

import importlib
import importlib.util
import inspect
from pathlib import Path
from typing import Dict, List, Optional, Any, Type
from datetime import datetime

from ..core.plugin import (
    Plugin, PluginAPI, PluginInfo, PluginMetadata, PluginStatus, PluginType
)
from ..services.logger import get_logger
from ..services.settings import get_settings
from ..services.db import get_session


class PluginManager:
    """Manages plugin loading, enabling, disabling, and execution."""
    
    def __init__(self):
        """Initialize plugin manager."""
        self.logger = get_logger()
        self.settings = get_settings()
        self.plugins: Dict[str, PluginInfo] = {}
        self.loaded_plugins: Dict[str, Plugin] = {}
        self.plugin_paths: List[Path] = []
        self.api: Optional[PluginAPI] = None
        
        # Initialize plugin API
        self._initialize_api()
        
        # Load plugin paths from settings
        self._load_plugin_paths()
    
    def _initialize_api(self):
        """Initialize plugin API with application services."""
        # Import here to avoid circular dependency
        def get_campaign_manager_func():
            from ..services import get_campaign_manager
            return get_campaign_manager()
        
        services = {
            'logger': self.logger,
            'settings': self.settings,
            'session': get_session,
            'campaign_manager': get_campaign_manager_func,
        }
        self.api = PluginAPI(services)
    
    def _load_plugin_paths(self):
        """Load plugin paths from settings or use defaults."""
        # Default plugin directory
        default_path = Path(self.settings.app_data_dir) / "plugins"
        default_path.mkdir(parents=True, exist_ok=True)
        
        # Add default path
        self.plugin_paths.append(default_path)
        
        # Add built-in plugins path
        builtin_path = Path(__file__).parent.parent / "plugins"
        if builtin_path.exists():
            self.plugin_paths.append(builtin_path)
        
        # Load custom paths from settings if available
        if hasattr(self.settings, 'plugin_paths'):
            for path_str in self.settings.plugin_paths:
                path = Path(path_str)
                if path.exists():
                    self.plugin_paths.append(path)
    
    def discover_plugins(self) -> List[Path]:
        """
        Discover all plugin files in plugin paths.
        
        Returns:
            List of plugin file paths
        """
        plugin_files = []
        for plugin_path in self.plugin_paths:
            if not plugin_path.exists():
                continue
            
            # Look for Python files
            for file_path in plugin_path.rglob("*.py"):
                # Skip __init__.py and test files
                if file_path.name.startswith("__") or "test" in file_path.name.lower():
                    continue
                plugin_files.append(file_path)
        
        return plugin_files
    
    def load_plugin(self, plugin_path: Path) -> Optional[PluginInfo]:
        """
        Load a plugin from a file path.
        
        Args:
            plugin_path: Path to plugin file
            
        Returns:
            PluginInfo if loaded successfully, None otherwise
        """
        try:
            # Import the module
            module_name = plugin_path.stem
            
            # Add parent directory to sys.path to allow relative imports
            import sys
            parent_dir = str(plugin_path.parent)
            if parent_dir not in sys.path:
                sys.path.insert(0, parent_dir)
            
            try:
                spec = importlib.util.spec_from_file_location(module_name, plugin_path)
                if spec is None or spec.loader is None:
                    raise ImportError(f"Could not load spec for {plugin_path}")
                
                module = importlib.util.module_from_spec(spec)
                
                # Set __package__ to allow relative imports
                if plugin_path.parent.name == "plugins":
                    module.__package__ = "app.plugins"
                else:
                    # Try to determine package from path
                    parts = plugin_path.parts
                    if "app" in parts:
                        app_idx = list(parts).index("app")
                        module.__package__ = ".".join(parts[app_idx:-1])
                
                spec.loader.exec_module(module)
            finally:
                # Remove from sys.path after loading
                if parent_dir in sys.path:
                    sys.path.remove(parent_dir)
            
            # Find Plugin subclass
            plugin_class = None
            for name, obj in inspect.getmembers(module):
                if (inspect.isclass(obj) and 
                    issubclass(obj, Plugin) and 
                    obj is not Plugin and
                    obj is not MessageFilterPlugin and
                    obj is not AnalyticsPlugin and
                    obj is not NotificationPlugin and
                    obj is not IntegrationPlugin):
                    plugin_class = obj
                    break
            
            if plugin_class is None:
                raise ValueError(f"No Plugin subclass found in {plugin_path}")
            
            # Try to instantiate plugin - Python's ABC will raise TypeError if abstract methods aren't implemented
            # We catch it and provide better error context
            try:
                plugin_instance = plugin_class(self.api)
            except TypeError as e:
                error_msg = str(e)
                if "abstract" in error_msg.lower() or "abstractmethod" in error_msg.lower():
                    # This is an abstract method error - log it and skip this plugin
                    self.logger.error(f"Error loading plugin {plugin_path.name}: {error_msg}")
                    return None
                else:
                    # Some other TypeError during instantiation
                    raise
            
            # Get metadata
            metadata = plugin_instance.metadata
            
            # Create plugin info
            plugin_info = PluginInfo(
                metadata=metadata,
                status=PluginStatus.LOADED,
                path=str(plugin_path),
                loaded_at=datetime.utcnow()
            )
            
            # Store plugin
            plugin_id = f"{metadata.name}@{metadata.version}"
            self.plugins[plugin_id] = plugin_info
            self.loaded_plugins[plugin_id] = plugin_instance
            
            # Call on_load
            plugin_instance.on_load()
            
            self.logger.info(f"Loaded plugin: {metadata.name} v{metadata.version}")
            return plugin_info
            
        except Exception as e:
            self.logger.error(f"Error loading plugin {plugin_path}: {e}")
            return None
    
    def enable_plugin(self, plugin_id: str) -> bool:
        """
        Enable a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if enabled successfully, False otherwise
        """
        if plugin_id not in self.loaded_plugins:
            self.logger.error(f"Plugin {plugin_id} not found")
            return False
        
        try:
            plugin = self.loaded_plugins[plugin_id]
            plugin.enable()
            
            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.ENABLED
                self.plugins[plugin_id].enabled_at = datetime.utcnow()
            
            self.logger.info(f"Enabled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error enabling plugin {plugin_id}: {e}")
            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.ERROR
                self.plugins[plugin_id].error_message = str(e)
            return False
    
    def disable_plugin(self, plugin_id: str) -> bool:
        """
        Disable a plugin.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if disabled successfully, False otherwise
        """
        if plugin_id not in self.loaded_plugins:
            self.logger.error(f"Plugin {plugin_id} not found")
            return False
        
        try:
            plugin = self.loaded_plugins[plugin_id]
            plugin.disable()
            
            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.DISABLED
            
            self.logger.info(f"Disabled plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error disabling plugin {plugin_id}: {e}")
            return False
    
    def unload_plugin(self, plugin_id: str) -> bool:
        """
        Unload a plugin completely.
        
        Args:
            plugin_id: Plugin identifier
            
        Returns:
            True if unloaded successfully, False otherwise
        """
        if plugin_id not in self.loaded_plugins:
            return False
        
        try:
            plugin = self.loaded_plugins[plugin_id]
            
            # Disable first if enabled
            if plugin.is_enabled:
                plugin.disable()
            
            # Call on_unload
            plugin.on_unload()
            
            # Remove from loaded plugins
            del self.loaded_plugins[plugin_id]
            
            if plugin_id in self.plugins:
                self.plugins[plugin_id].status = PluginStatus.UNLOADED
            
            self.logger.info(f"Unloaded plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error unloading plugin {plugin_id}: {e}")
            return False
    
    def get_plugin(self, plugin_id: str) -> Optional[Plugin]:
        """Get a plugin instance by ID."""
        return self.loaded_plugins.get(plugin_id)
    
    def get_plugin_info(self, plugin_id: str) -> Optional[PluginInfo]:
        """Get plugin information by ID."""
        return self.plugins.get(plugin_id)
    
    def list_plugins(self) -> List[PluginInfo]:
        """List all loaded plugins."""
        return list(self.plugins.values())
    
    def list_enabled_plugins(self) -> List[PluginInfo]:
        """List all enabled plugins."""
        return [info for info in self.plugins.values() if info.status == PluginStatus.ENABLED]
    
    def reload_all_plugins(self):
        """Reload all plugins."""
        self.logger.info("Reloading all plugins...")
        
        # Get current plugin IDs
        plugin_ids = list(self.loaded_plugins.keys())
        
        # Unload all
        for plugin_id in plugin_ids:
            self.unload_plugin(plugin_id)
        
        # Clear plugins
        self.plugins.clear()
        self.loaded_plugins.clear()
        
        # Discover and load plugins
        plugin_files = self.discover_plugins()
        for plugin_file in plugin_files:
            self.load_plugin(plugin_file)
        
        # Enable plugins that were previously enabled (from settings)
        if hasattr(self.settings, 'enabled_plugins'):
            for plugin_id in self.settings.enabled_plugins:
                if plugin_id in self.loaded_plugins:
                    self.enable_plugin(plugin_id)
    
    def set_plugin_config(self, plugin_id: str, config: Dict[str, Any]) -> bool:
        """
        Set configuration for a plugin.
        
        Args:
            plugin_id: Plugin identifier
            config: Configuration dictionary
            
        Returns:
            True if configuration set successfully, False otherwise
        """
        if plugin_id not in self.loaded_plugins:
            return False
        
        try:
            plugin = self.loaded_plugins[plugin_id]
            
            # Validate config
            is_valid, error = plugin.validate_config(config)
            if not is_valid:
                self.logger.error(f"Invalid config for {plugin_id}: {error}")
                return False
            
            # Set config
            plugin.set_config(config)
            
            # Update plugin info
            if plugin_id in self.plugins:
                self.plugins[plugin_id].config = config
            
            self.logger.info(f"Updated config for plugin: {plugin_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error setting config for {plugin_id}: {e}")
            return False


# Global plugin manager instance
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get the global plugin manager instance."""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager


def initialize_plugins():
    """Initialize and load all plugins."""
    manager = get_plugin_manager()
    manager.reload_all_plugins()

