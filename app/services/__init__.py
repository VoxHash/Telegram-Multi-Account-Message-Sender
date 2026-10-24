"""
Services module for the Telegram Multi-Account Message Sender.

Heavy services (campaign manager, plugins, health) are imported lazily so
lightweight modules such as ``settings`` and ``logger`` can load without
pulling ``app.core`` back into a partially initialized ``app.services``.
"""

from __future__ import annotations

from typing import Any

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
    # Plugin Registry / Marketplace
    "get_plugin_registry_service",
    "PluginRegistryService",
    # Optional read-only web companion
    "WebCompanionServer",
    "start_companion_from_settings",
    "maybe_autostart_companion_from_settings",
    "stop_companion",
    "is_companion_gui_owned",
    "run_web_monitor_cli",
]

# name -> (submodule, attribute)
_EXPORTS: dict[str, tuple[str, str]] = {
    "get_settings": (".settings", "get_settings"),
    "Settings": (".settings", "Settings"),
    "reload_settings": (".settings", "reload_settings"),
    "get_logger": (".logger", "get_logger"),
    "AppLogger": (".logger", "AppLogger"),
    "setup_logging": (".logger", "setup_logging"),
    "get_db_service": (".db", "get_db_service"),
    "initialize_database": (".db", "initialize_database"),
    "get_session": (".db", "get_session"),
    "get_async_session": (".db", "get_async_session"),
    "close_database": (".db", "close_database"),
    "health_check": (".db", "health_check"),
    "backup_database": (".db", "backup_database"),
    "restore_database": (".db", "restore_database"),
    "get_campaign_manager": (".campaign_manager", "get_campaign_manager"),
    "CampaignManager": (".campaign_manager", "CampaignManager"),
    "AccountHealthMonitor": (".account_health", "AccountHealthMonitor"),
    "HealthStatus": (".account_health", "HealthStatus"),
    "get_performance_monitor": (".performance", "get_performance_monitor"),
    "PerformanceMonitor": (".performance", "PerformanceMonitor"),
    "performance_timer": (".performance", "performance_timer"),
    "get_plugin_manager": (".plugin_manager", "get_plugin_manager"),
    "PluginManager": (".plugin_manager", "PluginManager"),
    "initialize_plugins": (".plugin_manager", "initialize_plugins"),
    "get_plugin_registry_service": (".plugin_registry", "get_plugin_registry_service"),
    "PluginRegistryService": (".plugin_registry", "PluginRegistryService"),
    "WebCompanionServer": (".web_companion", "WebCompanionServer"),
    "start_companion_from_settings": (".web_companion", "start_companion_from_settings"),
    "maybe_autostart_companion_from_settings": (
        ".web_companion",
        "maybe_autostart_companion_from_settings",
    ),
    "stop_companion": (".web_companion", "stop_companion"),
    "is_companion_gui_owned": (".web_companion", "is_companion_gui_owned"),
    "run_web_monitor_cli": (".web_companion", "run_web_monitor_cli"),
}


def __getattr__(name: str) -> Any:
    """Lazily import public exports on first access."""
    try:
        module_name, attr = _EXPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc
    from importlib import import_module

    value = getattr(import_module(module_name, __name__), attr)
    globals()[name] = value
    return value


def __dir__() -> list[str]:
    return sorted(set(globals()) | set(__all__))
