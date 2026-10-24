"""
Main entry point for the Telegram Multi-Account Message Sender.

This is the new production-grade version with GUI support.
"""

import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent / "app"
sys.path.insert(0, str(app_dir))

from app import __version__
from app.core.launch_args import filter_qt_argv, resolve_existing_backup_package
from app.services import initialize_database, get_settings, get_logger, initialize_plugins
# Explicitly import telegram_selector early to ensure PyInstaller includes it
from app.gui.widgets.telegram_selector import TelegramSelectorDialog  # noqa: F401
from app.gui.main import MainWindow

# Import all models to ensure they are registered with SQLModel
from app.models import Account, Campaign, Recipient, SendLog  # noqa: F401
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon


def main():
    """Main application entry point."""
    pending_backup = resolve_existing_backup_package(sys.argv)
    qt_argv = filter_qt_argv(sys.argv)

    # Initialize services
    initialize_database()
    settings = get_settings()
    logger = get_logger()

    # Initialize plugins
    initialize_plugins()

    logger.info("Starting Telegram Multi-Account Message Sender")
    if pending_backup is not None:
        logger.info(f"Opened via file association: {pending_backup}")

    # Create Qt application
    app = QApplication(qt_argv)
    app.setApplicationName("Telegram Multi-Account Message Sender")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("VoxHash")

    # Set application icon
    icon_path = Path(__file__).parent / "assets" / "icons" / "favicon.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    # Set application style
    app.setStyle('Fusion')

    # Create and show main window
    main_window = MainWindow(pending_backup_path=pending_backup)
    main_window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
