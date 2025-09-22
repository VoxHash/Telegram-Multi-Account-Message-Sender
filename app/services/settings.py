"""
Application settings management using Pydantic.
"""

import os
from pathlib import Path
from typing import Optional, List, Dict, Any
from enum import Enum

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class LogLevel(str, Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class Theme(str, Enum):
    """Theme enumeration."""
    AUTO = "auto"
    LIGHT = "light"
    DARK = "dark"


class AppEnvironment(str, Enum):
    """Application environment enumeration."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )
    
    # Application
    app_name: str = "Telegram Multi-Account Message Sender"
    app_version: str = "1.0.0"
    app_env: AppEnvironment = AppEnvironment.DEVELOPMENT
    debug: bool = False
    
    # Logging
    log_level: LogLevel = LogLevel.INFO
    log_to_file: bool = True
    log_file_max_size: int = 10 * 1024 * 1024  # 10MB
    log_file_backup_count: int = 5
    
    # Database
    database_url: str = "sqlite:///app_data/app.db"
    
    # Telegram API
    telegram_api_id: Optional[int] = None
    telegram_api_hash: Optional[str] = None
    
    # Rate Limiting
    default_rate_limits: int = 30  # messages per minute
    global_max_concurrency: int = 5
    max_messages_per_hour: int = 100
    max_messages_per_day: int = 1000
    
    # Warmup Settings
    warmup_enabled: bool = True
    warmup_messages: int = 5
    warmup_interval_minutes: int = 60
    
    # Proxies
    http_proxy: Optional[str] = None
    https_proxy: Optional[str] = None
    socks5_proxy: Optional[str] = None
    
    # Application Data Paths
    app_data_dir: str = "app_data"
    sessions_dir: str = "app_data/sessions"
    logs_dir: str = "app_data/logs"
    content_dir: str = "content"
    
    # UI Settings
    theme: Theme = Theme.AUTO
    window_width: int = 1200
    window_height: int = 800
    window_maximized: bool = False
    
    # Safety Settings
    respect_rate_limits: bool = True
    stop_on_error: bool = False
    max_retries: int = 3
    retry_delay_seconds: int = 5
    
    # Optional: Sentry
    sentry_dsn: Optional[str] = None
    
    # Optional: Additional settings
    custom_settings: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("app_data_dir", "sessions_dir", "logs_dir", "content_dir")
    def create_directories(cls, v):
        """Ensure directories exist."""
        Path(v).mkdir(parents=True, exist_ok=True)
        return v
    
    @validator("database_url")
    def validate_database_url(cls, v):
        """Validate database URL."""
        if not v.startswith(("sqlite:///", "postgresql://", "mysql://")):
            raise ValueError("Database URL must start with sqlite:///, postgresql://, or mysql://")
        return v
    
    @validator("telegram_api_id", pre=True)
    def validate_api_id(cls, v):
        """Validate Telegram API ID."""
        if v is None or v == "":
            return None
        try:
            parsed = int(v)
            if parsed <= 0:
                raise ValueError("Telegram API ID must be a positive integer")
            return parsed
        except (ValueError, TypeError):
            raise ValueError("Telegram API ID must be a positive integer")
    
    @validator("telegram_api_hash", pre=True)
    def validate_api_hash(cls, v):
        """Validate Telegram API hash."""
        if v is None or v == "":
            return None
        if not isinstance(v, str) or len(v) != 32:
            raise ValueError("Telegram API hash must be a 32-character string")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v
    
    @validator("theme")
    def validate_theme(cls, v):
        """Validate theme."""
        if isinstance(v, str):
            return Theme(v.lower())
        return v
    
    @validator("app_env")
    def validate_app_env(cls, v):
        """Validate application environment."""
        if isinstance(v, str):
            return AppEnvironment(v.lower())
        return v
    
    def get_database_path(self) -> Path:
        """Get database file path."""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            return Path(db_path)
        raise ValueError("Database path only available for SQLite")
    
    def get_sessions_path(self) -> Path:
        """Get sessions directory path."""
        return Path(self.sessions_dir)
    
    def get_logs_path(self) -> Path:
        """Get logs directory path."""
        return Path(self.logs_dir)
    
    def get_content_path(self) -> Path:
        """Get content directory path."""
        return Path(self.content_dir)
    
    def is_telegram_configured(self) -> bool:
        """Check if Telegram API is configured."""
        return self.telegram_api_id is not None and self.telegram_api_hash is not None
    
    def get_proxy_settings(self) -> Dict[str, Optional[str]]:
        """Get proxy settings as dictionary."""
        return {
            "http": self.http_proxy,
            "https": self.https_proxy,
            "socks5": self.socks5_proxy,
        }
    
    def get_rate_limits(self) -> Dict[str, int]:
        """Get rate limits as dictionary."""
        return {
            "per_minute": self.default_rate_limits,
            "per_hour": self.max_messages_per_hour,
            "per_day": self.max_messages_per_day,
            "global_concurrency": self.global_max_concurrency,
        }
    
    def get_warmup_settings(self) -> Dict[str, Any]:
        """Get warmup settings as dictionary."""
        return {
            "enabled": self.warmup_enabled,
            "messages": self.warmup_messages,
            "interval_minutes": self.warmup_interval_minutes,
        }
    
    def get_ui_settings(self) -> Dict[str, Any]:
        """Get UI settings as dictionary."""
        return {
            "theme": self.theme,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "window_maximized": self.window_maximized,
        }
    
    def get_safety_settings(self) -> Dict[str, Any]:
        """Get safety settings as dictionary."""
        return {
            "respect_rate_limits": self.respect_rate_limits,
            "stop_on_error": self.stop_on_error,
            "max_retries": self.max_retries,
            "retry_delay_seconds": self.retry_delay_seconds,
        }
    
    def is_development(self) -> bool:
        """Check if running in development mode."""
        return self.app_env == AppEnvironment.DEVELOPMENT
    
    def is_production(self) -> bool:
        """Check if running in production mode."""
        return self.app_env == AppEnvironment.PRODUCTION
    
    def get_log_file_path(self) -> Path:
        """Get log file path."""
        return self.get_logs_path() / "app.log"
    
    def get_error_log_file_path(self) -> Path:
        """Get error log file path."""
        return self.get_logs_path() / "error.log"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings


def reload_settings() -> Settings:
    """Reload application settings."""
    global settings
    settings = Settings()
    return settings
