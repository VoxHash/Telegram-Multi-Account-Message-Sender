"""
Logging service with rich console output and file logging.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

from rich.console import Console
from rich.logging import RichHandler
from rich.traceback import install

from .settings import get_settings, LogLevel


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for different log levels."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        log_color = self.COLORS.get(record.levelname, '')
        record.levelname = f"{log_color}{record.levelname}{self.RESET}"
        return super().format(record)


class AppLogger:
    """Application logger with rich console and file output."""
    
    def __init__(self, name: str = "telegram_sender"):
        self.name = name
        self.settings = get_settings()
        self.console = Console()
        self._setup_logging()
    
    def _setup_logging(self):
        """Set up logging configuration."""
        # Install rich traceback handler
        install(show_locals=True)
        
        # Create logger
        self.logger = logging.getLogger(self.name)
        
        # Get log level - handle both enum and string values
        if hasattr(self.settings.log_level, 'value'):
            log_level = self.settings.log_level.value
        else:
            log_level = str(self.settings.log_level)
        
        self.logger.setLevel(getattr(logging, log_level))
        
        # Set debug level if debug mode is enabled
        if self.settings.debug:
            self.logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Console handler with rich formatting
        console_handler = RichHandler(
            console=self.console,
            show_time=True,
            show_path=True,
            enable_link_path=True,
            markup=True,
        )
        console_handler.setLevel(getattr(logging, log_level))
        console_formatter = logging.Formatter(
            fmt="%(message)s",
            datefmt="[%X]"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for general logs
        if self.settings.log_to_file:
            log_file = self.settings.get_log_file_path()
            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_file,
                maxBytes=self.settings.log_file_max_size,
                backupCount=self.settings.log_file_backup_count,
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
            
            # Error file handler
            error_log_file = self.settings.get_error_log_file_path()
            error_handler = logging.handlers.RotatingFileHandler(
                filename=error_log_file,
                maxBytes=self.settings.log_file_max_size,
                backupCount=self.settings.log_file_backup_count,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            self.logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message."""
        self.logger.debug(message, **kwargs)
    
    def info(self, message: str, **kwargs):
        """Log info message."""
        self.logger.info(message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self.logger.warning(message, **kwargs)
    
    def error(self, message: str, **kwargs):
        """Log error message."""
        self.logger.error(message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self.logger.critical(message, **kwargs)
    
    def exception(self, message: str, **kwargs):
        """Log exception with traceback."""
        self.logger.exception(message, **kwargs)
    
    def log_telegram_event(self, event_type: str, account_id: int, message: str, **kwargs):
        """Log Telegram-specific event."""
        self.info(f"[bold blue]Telegram[/bold blue] [{event_type}] Account {account_id}: {message}", **kwargs)
    
    def log_campaign_event(self, event_type: str, campaign_id: int, message: str, **kwargs):
        """Log campaign-specific event."""
        self.info(f"[bold green]Campaign[/bold green] [{event_type}] Campaign {campaign_id}: {message}", **kwargs)
    
    def log_send_event(self, status: str, account_id: int, recipient_id: int, message: str, **kwargs):
        """Log message send event."""
        color = {
            "sent": "green",
            "failed": "red",
            "rate_limited": "yellow",
            "skipped": "blue",
            "pending": "cyan"
        }.get(status, "white")
        
        self.info(f"[bold {color}]Send[/bold {color}] [{status.upper()}] Account {account_id} -> Recipient {recipient_id}: {message}", **kwargs)
    
    def log_rate_limit(self, account_id: int, limit_type: str, current: int, max_limit: int, **kwargs):
        """Log rate limit information."""
        self.warning(f"[bold yellow]Rate Limit[/bold yellow] Account {account_id} {limit_type}: {current}/{max_limit}", **kwargs)
    
    def log_safety_event(self, event_type: str, message: str, **kwargs):
        """Log safety/compliance event."""
        self.warning(f"[bold red]Safety[/bold red] [{event_type}]: {message}", **kwargs)
    
    def log_performance(self, operation: str, duration_ms: float, **kwargs):
        """Log performance metrics."""
        self.debug(f"[bold magenta]Performance[/bold magenta] {operation}: {duration_ms:.2f}ms", **kwargs)
    
    def reload_settings(self):
        """Reload logger with updated settings."""
        self.settings = get_settings()
        self._setup_logging()
    
    def get_log_file_path(self) -> Path:
        """Get log file path."""
        return self.settings.get_log_file_path()
    
    def get_error_log_file_path(self) -> Path:
        """Get error log file path."""
        return self.settings.get_error_log_file_path()
    
    def export_logs(self, start_time: Optional[datetime] = None, end_time: Optional[datetime] = None) -> str:
        """Export logs for a time period."""
        # This would implement log export functionality
        # For now, return a placeholder
        return "Log export functionality not yet implemented"


# Global logger instance
logger = AppLogger()


def get_logger() -> AppLogger:
    """Get application logger."""
    return logger


def setup_logging(name: str = "telegram_sender") -> AppLogger:
    """Set up logging for a specific module."""
    return AppLogger(name)


def log_telegram_event(event_type: str, account_id: int, message: str, **kwargs):
    """Log Telegram event using global logger."""
    logger.log_telegram_event(event_type, account_id, message, **kwargs)


def log_campaign_event(event_type: str, campaign_id: int, message: str, **kwargs):
    """Log campaign event using global logger."""
    logger.log_campaign_event(event_type, campaign_id, message, **kwargs)


def log_send_event(status: str, account_id: int, recipient_id: int, message: str, **kwargs):
    """Log send event using global logger."""
    logger.log_send_event(status, account_id, recipient_id, message, **kwargs)


def log_rate_limit(account_id: int, limit_type: str, current: int, max_limit: int, **kwargs):
    """Log rate limit using global logger."""
    logger.log_rate_limit(account_id, limit_type, current, max_limit, **kwargs)


def log_safety_event(event_type: str, message: str, **kwargs):
    """Log safety event using global logger."""
    logger.log_safety_event(event_type, message, **kwargs)


def log_performance(operation: str, duration_ms: float, **kwargs):
    """Log performance using global logger."""
    logger.log_performance(operation, duration_ms, **kwargs)


def reload_logger():
    """Reload the global logger with updated settings."""
    global logger
    logger.reload_settings()
