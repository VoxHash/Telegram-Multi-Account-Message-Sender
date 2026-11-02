"""Unit tests for Linux / Qt desktop identity constants and wiring."""

from unittest.mock import MagicMock

from app.core.desktop_identity import (
    APP_NAME,
    DESKTOP_FILE_ID,
    ORGANIZATION_DOMAIN,
    ORGANIZATION_NAME,
    STARTUP_WM_CLASS,
    apply_desktop_identity,
)


class TestDesktopIdentityConstants:
    def test_desktop_id_is_reverse_dns_and_stable(self):
        assert DESKTOP_FILE_ID == "dev.voxhash.telegram-multi-account-sender"
        assert STARTUP_WM_CLASS == DESKTOP_FILE_ID
        assert "python" not in DESKTOP_FILE_ID.lower()

    def test_organization_domain_is_app_specific(self):
        assert ORGANIZATION_NAME == "VoxHash"
        assert ORGANIZATION_DOMAIN == "telegram-multi-account-sender.voxhash.dev"
        assert APP_NAME == "Telegram Multi-Account Message Sender"


class TestApplyDesktopIdentity:
    def test_apply_sets_desktop_file_name_and_org(self):
        app = MagicMock()
        apply_desktop_identity(app, version="1.2.52")

        app.setOrganizationName.assert_called_once_with(ORGANIZATION_NAME)
        app.setOrganizationDomain.assert_called_once_with(ORGANIZATION_DOMAIN)
        app.setApplicationName.assert_called_once_with(APP_NAME)
        app.setApplicationDisplayName.assert_called_once_with(APP_NAME)
        app.setApplicationVersion.assert_called_once_with("1.2.52")
        app.setDesktopFileName.assert_called_once_with(DESKTOP_FILE_ID)
