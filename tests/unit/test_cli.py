"""
Unit tests for CLI module surface (entrypoint wiring without launching Qt).
"""

import importlib
from unittest.mock import MagicMock, patch


class TestCliEntrypoint:
    def test_cli_module_exposes_main(self):
        # Importing app.cli pulls Qt; ensure main is callable once imported.
        cli = importlib.import_module("app.cli")
        assert callable(cli.main)

    def test_main_wires_database_settings_and_window(self):
        cli = importlib.import_module("app.cli")

        mock_app = MagicMock()
        mock_app.exec_.return_value = 0
        mock_window = MagicMock()

        with (
            patch.object(cli, "initialize_database") as init_db,
            patch.object(cli, "get_settings") as get_settings,
            patch.object(cli, "get_logger") as get_logger,
            patch.object(cli, "QApplication", return_value=mock_app) as qapp,
            patch.object(cli, "MainWindow", return_value=mock_window) as main_window,
            patch.object(cli.sys, "exit") as sys_exit,
        ):
            get_logger.return_value = MagicMock()
            cli.main()

            init_db.assert_called_once_with()
            get_settings.assert_called_once_with()
            qapp.assert_called_once()
            mock_app.setApplicationName.assert_called_once()
            mock_app.setApplicationVersion.assert_called_once()
            main_window.assert_called_once_with()
            mock_window.show.assert_called_once_with()
            mock_app.exec_.assert_called_once_with()
            sys_exit.assert_called_once_with(0)
