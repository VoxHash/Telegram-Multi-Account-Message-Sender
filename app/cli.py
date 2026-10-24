#!/usr/bin/env python3
"""
Command-line interface for Telegram Multi-Account Message Sender.
"""

import sys
from pathlib import Path

# Add app directory to Python path
app_dir = Path(__file__).parent
sys.path.insert(0, str(app_dir))

from app.services.handoff import parse_handoff_argv, run_handoff_cli  # noqa: E402
from app.services.plugin_sdk import (  # noqa: E402
    parse_plugin_validate_argv,
    run_plugin_validate_cli,
)
from app.services.web_companion import parse_web_monitor_argv, run_web_monitor_cli  # noqa: E402


def main() -> None:
    """Main entry point for the CLI."""
    is_web, _, _, _ = parse_web_monitor_argv(sys.argv)
    if is_web:
        raise SystemExit(run_web_monitor_cli(sys.argv))

    is_handoff, *_ = parse_handoff_argv(sys.argv)
    if is_handoff:
        raise SystemExit(run_handoff_cli(sys.argv))

    is_plugin_validate, *_ = parse_plugin_validate_argv(sys.argv)
    if is_plugin_validate:
        raise SystemExit(run_plugin_validate_cli(sys.argv))

    from app import __version__
    from app.core.launch_args import filter_qt_argv, resolve_existing_backup_package
    from app.services import initialize_database, get_settings, get_logger
    from app.gui.main import MainWindow
    from PyQt5.QtWidgets import QApplication

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
