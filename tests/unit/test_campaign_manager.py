"""
Unit tests for campaign manager critical paths.
"""

from unittest.mock import MagicMock, patch

import pytest

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType
from app.models import (
    Campaign,
    CampaignStatus,
    CampaignType,
    MessageType,
    Recipient,
    RecipientSource,
    RecipientStatus,
    RecipientType,
)
from app.services import get_session


@pytest.fixture
def campaign_manager(temp_db):
    """Campaign manager with timers disabled for headless tests."""
    mock_timer = MagicMock()
    mock_timer.return_value.timeout = MagicMock(return_value=mock_timer.return_value)
    mock_timer.return_value.start = MagicMock()
    mock_timer.return_value.stop = MagicMock()

    with patch("app.services.campaign_manager.QTimer", mock_timer):
        from app.services.campaign_manager import CampaignManager

        manager = CampaignManager()
        yield manager


def _create_campaign(
    *,
    name: str = "Test Campaign",
    status: CampaignStatus = CampaignStatus.DRAFT,
    total_recipients: int = 1,
    failed_count: int = 0,
    recipient_source: str = "manual",
) -> Campaign:
    campaign = Campaign(
        name=name,
        message_text="Hello",
        campaign_type=CampaignType.IMMEDIATE,
        message_type=MessageType.TEXT,
        status=status,
        total_recipients=total_recipients,
        failed_count=failed_count,
        recipient_source=recipient_source,
    )
    with get_session() as session:
        session.add(campaign)
        session.commit()
        session.refresh(campaign)
    return campaign


def _create_recipient(*, username: str) -> Recipient:
    recipient = Recipient(
        recipient_type=RecipientType.USER,
        username=username,
        source=RecipientSource.MANUAL,
        status=RecipientStatus.ACTIVE,
    )
    with get_session() as session:
        session.add(recipient)
        session.commit()
        session.refresh(recipient)
    return recipient


class TestCampaignManager:
    """Tests for CampaignManager service methods."""

    def test_get_campaign_status_unknown(self, campaign_manager):
        assert campaign_manager.get_campaign_status(99999) == "unknown"

    def test_is_campaign_running_false_by_default(self, campaign_manager):
        assert campaign_manager.is_campaign_running(1) is False

    def test_can_retry_campaign_with_failures(self, campaign_manager):
        campaign = _create_campaign(failed_count=3, status=CampaignStatus.COMPLETED)

        assert campaign_manager.can_retry_campaign(campaign.id) is True

    def test_can_retry_campaign_failed_status(self, campaign_manager):
        campaign = _create_campaign(status=CampaignStatus.FAILED)

        assert campaign_manager.can_retry_campaign(campaign.id) is True

    def test_duplicate_campaign_creates_draft_copy(self, campaign_manager):
        original = _create_campaign(name="Original", status=CampaignStatus.COMPLETED)

        new_id = campaign_manager.duplicate_campaign(original.id)

        assert new_id is not None
        with get_session() as session:
            copy = session.get(Campaign, new_id)
            assert copy is not None
            assert copy.name == "Original (Copy)"
            assert copy.status == CampaignStatus.DRAFT
            assert copy.sent_count == 0
            assert copy.failed_count == 0

    def test_calculate_recipient_hash_changes_when_recipients_change(self, campaign_manager):
        campaign = _create_campaign(recipient_source="manual")
        _create_recipient(username="user_a")

        with get_session() as session:
            db_campaign = session.get(Campaign, campaign.id)

            first_hash = campaign_manager._calculate_recipient_hash(db_campaign)

            session.add(
                Recipient(
                    recipient_type=RecipientType.USER,
                    username="user_b",
                    source=RecipientSource.MANUAL,
                    status=RecipientStatus.ACTIVE,
                )
            )
            session.commit()
            session.refresh(db_campaign)

            second_hash = campaign_manager._calculate_recipient_hash(db_campaign)

        assert first_hash
        assert second_hash
        assert first_hash != second_hash

    def test_start_campaign_returns_false_when_not_found(self, campaign_manager):
        assert campaign_manager.start_campaign(99999) is False

    def test_start_campaign_returns_false_when_cannot_start(self, campaign_manager):
        campaign = _create_campaign(total_recipients=0, status=CampaignStatus.DRAFT)

        assert campaign_manager.start_campaign(campaign.id) is False

    def test_apply_message_filters_uses_recipient_type(self, campaign_manager):
        recipient = _create_recipient(username="self_account")
        captured_recipient_data = {}

        class CapturingFilterPlugin(MessageFilterPlugin):
            @property
            def metadata(self) -> PluginMetadata:
                return PluginMetadata(
                    name="Capturing Filter",
                    version="1.0.0",
                    description="Captures recipient payload in tests",
                    author="tests",
                    plugin_type=PluginType.FILTER,
                )

            def filter_message(self, message, recipient_data):
                captured_recipient_data.update(recipient_data)
                return message

        plugin = CapturingFilterPlugin(api=MagicMock())
        plugin_info = MagicMock()
        plugin_info.metadata.name = "Capturing Filter"
        plugin_info.metadata.version = "1.0.0"

        campaign_manager.plugin_manager.list_enabled_plugins = MagicMock(
            return_value=[plugin_info]
        )
        campaign_manager.plugin_manager.get_plugin = MagicMock(return_value=plugin)

        filtered_message = campaign_manager._apply_message_filters("Hello", recipient)

        assert filtered_message == "Hello"
        assert captured_recipient_data["type"] == RecipientType.USER.value
