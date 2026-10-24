#!/usr/bin/env python3
"""
Command-line interface for Telegram Multi-Account Message Sender.
"""

import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app import __version__  # noqa: E402
from app.core.launch_args import filter_qt_argv, resolve_existing_backup_package  # noqa: E402
from app.services import initialize_database, get_settings, get_logger  # noqa: E402
from app.gui.main import MainWindow  # noqa: E402

# Import all models to ensure they are registered with SQLModel
from PyQt5.QtWidgets import QApplication  # noqa: E402


def main() -> None:
    """Main entry point for the CLI."""
    pending_backup = resolve_existing_backup_package(sys.argv)
    qt_argv = filter_qt_argv(sys.argv)

    # Initialize database
    initialize_database()

    # Get settings and logger
    get_settings()
    logger = get_logger()

    logger.info("Starting Telegram Multi-Account Message Sender...")
    if pending_backup is not None:
        logger.info(f"Opened via file association: {pending_backup}")

    # Create QApplication
    app = QApplication(qt_argv)
    app.setApplicationName("Telegram Multi-Account Message Sender")
    app.setApplicationVersion(__version__)

    # Create and show main window
    main_window = MainWindow(pending_backup_path=pending_backup)
    main_window.show()

    # Run application
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
