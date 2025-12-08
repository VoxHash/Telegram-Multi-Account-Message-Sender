"""
Services module for the Telegram Multi-Account Message Sender.
"""

from .settings import get_settings, Settings, reload_settings
from .logger import get_logger, AppLogger, setup_logging
from .db import (
    get_db_service, 
    initialize_database, 
    get_session, 
    get_async_session,
    close_database,
    health_check,
    backup_database,
    restore_database
)
from .campaign_manager import get_campaign_manager, CampaignManager
from .account_health import AccountHealthMonitor, HealthStatus
from .performance import get_performance_monitor, PerformanceMonitor, performance_timer
from .plugin_manager import get_plugin_manager, PluginManager, initialize_plugins

__all__ = [
    # Settings
    "get_settings",
    "Settings", 
    "reload_settings",
    
    # Logging
    "get_logger",
    "AppLogger",
    "setup_logging",
    
    # Database
    "get_db_service",
    "initialize_database",
    "get_session",
    "get_async_session", 
    "close_database",
    "health_check",
    "backup_database",
    "restore_database",
    
    # Campaign Management
    "get_campaign_manager",
    "CampaignManager",
    
    # Account Health
    "AccountHealthMonitor",
    "HealthStatus",
    
    # Performance
    "get_performance_monitor",
    "PerformanceMonitor",
    "performance_timer",
    
    # Plugin Management
    "get_plugin_manager",
    "PluginManager",
    "initialize_plugins",
]
