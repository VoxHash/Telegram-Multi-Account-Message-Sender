"""
Pytest configuration and fixtures.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, AsyncMock

from app.services import initialize_database, get_settings
from app.models import Account, Campaign, Recipient


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    # Use in-memory SQLite for testing
    import os
    os.environ["DATABASE_URL"] = "sqlite:///:memory:"
    
    # Initialize database
    initialize_database()
    
    yield
    
    # Cleanup
    from app.services import close_database
    close_database()


@pytest.fixture
def sample_account():
    """Create a sample account for testing."""
    return Account(
        name="Test Account",
        phone_number="+1234567890",
        api_id=12345,
        api_hash="test_hash",
        session_path="test_session"
    )


@pytest.fixture
def sample_campaign():
    """Create a sample campaign for testing."""
    return Campaign(
        name="Test Campaign",
        message_text="Hello, {{first_name}}!",
        total_recipients=10
    )


@pytest.fixture
def sample_recipient():
    """Create a sample recipient for testing."""
    return Recipient(
        username="testuser",
        first_name="Test",
        last_name="User"
    )


@pytest.fixture
def mock_telegram_client():
    """Create a mock Telegram client."""
    client = Mock()
    client.is_ready = Mock(return_value=True)
    client.send_message = AsyncMock(return_value={"success": True, "message_id": 123})
    client.get_status = Mock(return_value={"connected": True, "authorized": True})
    return client
