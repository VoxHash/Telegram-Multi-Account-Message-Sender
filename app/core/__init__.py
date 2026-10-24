"""
Core module for the Telegram Multi-Account Message Sender.

Exports are resolved lazily so submodule imports such as
``from app.core.spintax import SpintaxProcessor`` do not pull in Telethon,
the message engine, or ``app.services`` (which would re-enter ``app.core``).
"""

from __future__ import annotations

from typing import Any

__all__ = [
    # Telegram Client
    "TelegramClientManager",
    "TelegramClientWrapper",
    # Message Engine
    "MessageEngine",
    "CampaignRunner",
    # Rate Limiting
    "Throttler",
    "RateLimiter",
    # Spintax
    "SpintaxProcessor",
    # Compliance
    "ComplianceChecker",
    "SafetyGuard",
    # Analytics
    "AnalyticsCollector",
    "CampaignAnalytics",
    # Message Forwarding
    "MessageForwarder",
    # Plugin System
    "Plugin",
    "PluginAPI",
    "PluginMetadata",
    "PluginInfo",
    "PluginStatus",
    "PluginType",
    "MessageFilterPlugin",
    "AnalyticsPlugin",
    "NotificationPlugin",
    "IntegrationPlugin",
]

# name -> (submodule, attribute)
_EXPORTS: dict[str, tuple[str, str]] = {
    "TelegramClientManager": (".telethon_client", "TelegramClientManager"),
    "TelegramClientWrapper": (".telethon_client", "TelegramClientWrapper"),
    "MessageEngine": (".engine", "MessageEngine"),
    "CampaignRunner": (".engine", "CampaignRunner"),
    "Throttler": (".throttler", "Throttler"),
    "RateLimiter": (".throttler", "RateLimiter"),
    "SpintaxProcessor": (".spintax", "SpintaxProcessor"),
    "ComplianceChecker": (".compliance", "ComplianceChecker"),
    "SafetyGuard": (".compliance", "SafetyGuard"),
    "AnalyticsCollector": (".analytics", "AnalyticsCollector"),
    "CampaignAnalytics": (".analytics", "CampaignAnalytics"),
    "MessageForwarder": (".message_forwarder", "MessageForwarder"),
    "Plugin": (".plugin", "Plugin"),
    "PluginAPI": (".plugin", "PluginAPI"),
    "PluginMetadata": (".plugin", "PluginMetadata"),
    "PluginInfo": (".plugin", "PluginInfo"),
    "PluginStatus": (".plugin", "PluginStatus"),
    "PluginType": (".plugin", "PluginType"),
    "MessageFilterPlugin": (".plugin", "MessageFilterPlugin"),
    "AnalyticsPlugin": (".plugin", "AnalyticsPlugin"),
    "NotificationPlugin": (".plugin", "NotificationPlugin"),
    "IntegrationPlugin": (".plugin", "IntegrationPlugin"),
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
