"""
Main entry point for the Telegram Multi-Account Message Sender.

This is the new production-grade version with GUI support.
"""

import sys
import asyncio
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app.services import initialize_database, get_settings, get_logger
from app.gui.main import MainWindow

# Import all models to ensure they are registered with SQLModel
from app.models import Account, Campaign, Recipient, SendLog
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon


def main():
    """Main application entry point."""
    # Initialize services
    initialize_database()
    settings = get_settings()
    logger = get_logger()
    
    logger.info("Starting Telegram Multi-Account Message Sender")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("Telegram Multi-Account Message Sender")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("VoxHash")
    
    # Set application icon
    icon_path = Path(__file__).parent / "assets" / "icons" / "favicon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))
    
    # Set application style
    app.setStyle('Fusion')
    
    # Create and show main window
    main_window = MainWindow()
    main_window.show()
    
    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()