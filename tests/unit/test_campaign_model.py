"""
Unit tests for Campaign lifecycle helpers and progress math.
"""

from app.models import Campaign, CampaignStatus


def _campaign(**overrides) -> Campaign:
    data = {
        "name": "Lifecycle",
        "message_text": "Hello",
        "total_recipients": 10,
        "status": CampaignStatus.DRAFT,
        "is_active": True,
        "is_deleted": False,
        "sent_count": 0,
        "failed_count": 0,
        "skipped_count": 0,
        "progress_percentage": 0.0,
    }
    data.update(overrides)
    return Campaign(**data)


class TestCampaignLifecycle:
    def test_can_start_draft_with_recipients(self):
        assert _campaign().can_start() is True

    def test_cannot_start_without_recipients(self):
        assert _campaign(total_recipients=0).can_start() is False

    def test_cannot_start_when_running(self):
        assert _campaign(status=CampaignStatus.RUNNING).can_start() is False

    def test_cannot_start_inactive(self):
        assert _campaign(is_active=False).can_start() is False

    def test_can_pause_only_when_running(self):
        assert _campaign(status=CampaignStatus.RUNNING).can_pause() is True
        assert _campaign(status=CampaignStatus.DRAFT).can_pause() is False

    def test_can_resume_only_when_paused(self):
        assert _campaign(status=CampaignStatus.PAUSED).can_resume() is True
        assert _campaign(status=CampaignStatus.RUNNING).can_resume() is False

    def test_can_stop_running_or_paused(self):
        assert _campaign(status=CampaignStatus.RUNNING).can_stop() is True
        assert _campaign(status=CampaignStatus.PAUSED).can_stop() is True
        assert _campaign(status=CampaignStatus.DRAFT).can_stop() is False

    def test_update_progress(self):
        c = _campaign(sent_count=4, failed_count=1, skipped_count=0, total_recipients=10)
        c.update_progress()
        assert c.progress_percentage == 50.0

    def test_update_progress_zero_recipients(self):
        c = _campaign(total_recipients=0, sent_count=1)
        c.update_progress()
        assert c.progress_percentage == 0.0
