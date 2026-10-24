"""
Unit tests for CLI module surface (entrypoint wiring without launching Qt).
"""

import importlib
from unittest.mock import MagicMock, patch


class TestCliEntrypoint:
    def test_cli_module_exposes_main(self):
        # Importing app.cli no longer pulls Qt at import time (web-monitor path).
        cli = importlib.import_module("app.cli")
        assert callable(cli.main)

    def test_main_wires_database_settings_and_window(self):
        cli = importlib.import_module("app.cli")

        mock_app = MagicMock()
        mock_app.exec_.return_value = 0
        mock_window = MagicMock()

        with (
            patch("app.services.initialize_database") as init_db,
            patch("app.services.get_settings") as get_settings,
            patch("app.services.get_logger") as get_logger,
            patch("PyQt5.QtWidgets.QApplication", return_value=mock_app) as qapp,
            patch("app.gui.main.MainWindow", return_value=mock_window) as main_window,
            patch.object(cli.sys, "exit") as sys_exit,
            patch.object(cli.sys, "argv", ["telegram-sender"]),
        ):
            get_logger.return_value = MagicMock()
            cli.main()

            init_db.assert_called_once_with()
            get_settings.assert_called_once_with()
            qapp.assert_called_once()
            mock_app.setApplicationName.assert_called_once()
            mock_app.setApplicationVersion.assert_called_once()
            main_window.assert_called_once_with(pending_backup_path=None)
            mock_window.show.assert_called_once_with()
            mock_app.exec_.assert_called_once_with()
            sys_exit.assert_called_once_with(0)
