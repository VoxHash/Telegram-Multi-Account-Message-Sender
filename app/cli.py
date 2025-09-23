#!/usr/bin/env python3
"""
Command-line interface for Telegram Multi-Account Message Sender.
"""

import sys
import asyncio
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.services import initialize_database, get_settings, get_logger
from app.gui.main import MainWindow

# Import all models to ensure they are registered with SQLModel
from app.models import Account, Campaign, Recipient, SendLog
from PyQt5.QtWidgets import QApplication


def main():
    """Main entry point for the CLI."""
    # Initialize database
    initialize_database()
    
    # Get settings and logger
    settings = get_settings()
    logger = get_logger()
    
    logger.info("Starting Telegram Multi-Account Message Sender...")
    
    # Create QApplication
    app = QApplication(sys.argv)
    app.setApplicationName("Telegram Multi-Account Message Sender")
    app.setApplicationVersion("1.2.1")
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()