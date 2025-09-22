"""
Core module for the Telegram Multi-Account Message Sender.

This module contains the core business logic including:
- Telegram client management
- Message sending engine
- Rate limiting and throttling
- Spintax processing
- Compliance and safety features
- Analytics and reporting
"""

from .telethon_client import TelegramClientManager, TelegramClientWrapper
from .engine import MessageEngine, CampaignRunner
from .throttler import Throttler, RateLimiter
from .spintax import SpintaxProcessor
from .compliance import ComplianceChecker, SafetyGuard
from .analytics import AnalyticsCollector, CampaignAnalytics

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
]
