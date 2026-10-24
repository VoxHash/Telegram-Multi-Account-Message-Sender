"""
Unit tests for campaign message preparation and filter plugin payloads.
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock

import pytest

from app.core.plugin import MessageFilterPlugin, PluginMetadata, PluginType
from app.core.spintax import SpintaxProcessor
from app.models import Campaign, CampaignStatus, Recipient, RecipientType
from app.services.campaign_manager import CampaignManager


class UppercaseFilter(MessageFilterPlugin):
    """Test filter that uppercases text and records recipient payload."""

    def __init__(self):
        self.api = None
        self._enabled = True
        self._config = {}
        self.last_recipient: Optional[Dict[str, Any]] = None

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="uppercase-filter",
            version="1.0.0",
            description="test",
            author="test",
            plugin_type=PluginType.FILTER,
        )

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        self.last_recipient = recipient
        return message.upper()


class DropFilter(MessageFilterPlugin):
    """Filter that drops messages containing BLOCK."""

    def __init__(self):
        self.api = None
        self._enabled = True
        self._config = {}

    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="drop-filter",
            version="1.0.0",
            description="test",
            author="test",
            plugin_type=PluginType.FILTER,
        )

    def filter_message(self, message: str, recipient: Dict[str, Any]) -> Optional[str]:
        if "BLOCK" in message:
            return None
        return message


def _plugin_info(plugin: MessageFilterPlugin):
    info = MagicMock()
    info.metadata = plugin.metadata
    return info


def _make_manager(plugins: list[MessageFilterPlugin]) -> CampaignManager:
    """Build a CampaignManager without running QObject / timer setup."""
    manager = CampaignManager.__new__(CampaignManager)
    manager.logger = MagicMock()
    manager.spintax_processor = SpintaxProcessor(seed=42)
    manager.plugin_manager = MagicMock()
    manager.plugin_manager.list_enabled_plugins.return_value = [
        _plugin_info(p) for p in plugins
    ]

    def get_plugin(key: str):
        for plugin in plugins:
            expected = f"{plugin.metadata.name}@{plugin.metadata.version}"
            if key == expected:
                return plugin
        return None

    manager.plugin_manager.get_plugin.side_effect = get_plugin
    return manager


@pytest.fixture
def recipient():
    return Recipient(
        id=7,
        username="alice",
        first_name="Alice",
        last_name="Smith",
        phone_number="+15551234567",
        recipient_type=RecipientType.USER,
    )


@pytest.fixture
def campaign():
    return Campaign(
        name="Filter Campaign",
        message_text="Hello {name}",
        use_spintax=False,
        total_recipients=1,
        status=CampaignStatus.DRAFT,
        is_active=True,
        is_deleted=False,
    )


class TestMessageFilterPayloads:
    def test_filter_receives_recipient_payload(self, recipient):
        filt = UppercaseFilter()
        manager = _make_manager([filt])

        result = manager._apply_message_filters("hello world", recipient)

        assert result == "HELLO WORLD"
        assert filt.last_recipient == {
            "id": 7,
            "first_name": "Alice",
            "last_name": "Smith",
            "username": "alice",
            "phone_number": "+15551234567",
            "type": RecipientType.USER.value,
        }

    def test_filter_can_drop_message(self, recipient):
        manager = _make_manager([DropFilter()])
        assert manager._apply_message_filters("please BLOCK this", recipient) is None
        assert manager._apply_message_filters("ok to send", recipient) == "ok to send"

    def test_empty_message_skips_filters(self, recipient):
        filt = UppercaseFilter()
        manager = _make_manager([filt])
        assert manager._apply_message_filters("", recipient) == ""
        assert filt.last_recipient is None

    def test_prepare_message_personalizes_and_filters(self, campaign, recipient):
        filt = UppercaseFilter()
        manager = _make_manager([filt])

        result = manager._prepare_message(campaign, recipient)

        assert result == "HELLO ALICE SMITH"
        assert filt.last_recipient["username"] == "alice"

    def test_prepare_message_uses_preexpanded_text(self, campaign, recipient):
        manager = _make_manager([])
        result = manager._prepare_message(
            campaign, recipient, preexpanded_text="Hi {username}"
        )
        assert result == "Hi alice"

    def test_prepare_message_applies_spintax_when_enabled(self, recipient):
        campaign = Campaign(
            name="Spin",
            message_text="Hey {A|A}",
            use_spintax=True,
            total_recipients=1,
            status=CampaignStatus.DRAFT,
            is_active=True,
            is_deleted=False,
        )
        manager = _make_manager([])
        result = manager._prepare_message(campaign, recipient)
        assert result == "Hey A"
