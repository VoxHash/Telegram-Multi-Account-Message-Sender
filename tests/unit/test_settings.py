"""
Unit tests for Pydantic v2 Settings validators and helpers.
"""

import pytest
from pydantic import ValidationError

from app.services.settings import (
    AppEnvironment,
    Language,
    LogLevel,
    Settings,
    Theme,
)


@pytest.fixture
def settings_kwargs(tmp_path, monkeypatch):
    """Minimal kwargs that avoid mutating shared app_data paths unexpectedly."""
    data = tmp_path / "data"
    sessions = tmp_path / "sessions"
    logs = tmp_path / "logs"
    content = tmp_path / "content"
    # Prevent env from overriding test values
    for key in (
        "TELEGRAM_API_ID",
        "TELEGRAM_API_HASH",
        "DATABASE_URL",
        "LOG_LEVEL",
        "THEME",
        "APP_ENV",
        "LANGUAGE",
        "APP_DATA_DIR",
        "SESSIONS_DIR",
        "LOGS_DIR",
        "CONTENT_DIR",
    ):
        monkeypatch.delenv(key, raising=False)
    return {
        "app_data_dir": str(data),
        "sessions_dir": str(sessions),
        "logs_dir": str(logs),
        "content_dir": str(content),
        "database_url": f"sqlite:///{tmp_path / 'test.db'}",
    }


class TestSettingsValidators:
    def test_creates_directories(self, settings_kwargs):
        s = Settings(**settings_kwargs)
        assert (s.app_data_dir and __import__("pathlib").Path(s.app_data_dir).is_dir())
        assert __import__("pathlib").Path(s.sessions_dir).is_dir()
        assert __import__("pathlib").Path(s.logs_dir).is_dir()
        assert __import__("pathlib").Path(s.content_dir).is_dir()

    def test_rejects_invalid_database_url(self, settings_kwargs):
        settings_kwargs["database_url"] = "redis://localhost"
        with pytest.raises(ValidationError):
            Settings(**settings_kwargs)

    def test_api_id_empty_becomes_none(self, settings_kwargs):
        s = Settings(**settings_kwargs, telegram_api_id="")
        assert s.telegram_api_id is None

    def test_api_id_string_parsed(self, settings_kwargs):
        s = Settings(**settings_kwargs, telegram_api_id="12345")
        assert s.telegram_api_id == 12345

    def test_api_id_rejects_non_positive(self, settings_kwargs):
        with pytest.raises(ValidationError):
            Settings(**settings_kwargs, telegram_api_id=0)

    def test_api_hash_length(self, settings_kwargs):
        with pytest.raises(ValidationError):
            Settings(**settings_kwargs, telegram_api_hash="short")
        s = Settings(**settings_kwargs, telegram_api_hash="a" * 32)
        assert s.telegram_api_hash == "a" * 32

    def test_log_level_case_insensitive(self, settings_kwargs):
        s = Settings(**settings_kwargs, log_level="debug")
        assert s.log_level == LogLevel.DEBUG

    def test_theme_case_insensitive(self, settings_kwargs):
        s = Settings(**settings_kwargs, theme="DRACULA")
        assert s.theme == Theme.DRACULA

    def test_app_env_case_insensitive(self, settings_kwargs):
        s = Settings(**settings_kwargs, app_env="PRODUCTION")
        assert s.app_env == AppEnvironment.PRODUCTION
        assert s.is_production()

    def test_language_fallback_on_unknown(self, settings_kwargs):
        s = Settings(**settings_kwargs, language="xx")
        assert s.language == Language.ENGLISH

    def test_language_empty_defaults_english(self, settings_kwargs):
        s = Settings(**settings_kwargs, language="")
        assert s.language == Language.ENGLISH

    def test_is_telegram_configured(self, settings_kwargs):
        s = Settings(**settings_kwargs)
        assert not s.is_telegram_configured()
        s2 = Settings(
            **settings_kwargs,
            telegram_api_id=1,
            telegram_api_hash="b" * 32,
        )
        assert s2.is_telegram_configured()

    def test_get_rate_limits_shape(self, settings_kwargs):
        s = Settings(**settings_kwargs)
        limits = s.get_rate_limits()
        assert set(limits) == {
            "per_minute",
            "per_hour",
            "per_day",
            "global_concurrency",
        }

    def test_get_proxy_settings_shape(self, settings_kwargs):
        s = Settings(**settings_kwargs, http_proxy="http://127.0.0.1:8080")
        proxies = s.get_proxy_settings()
        assert proxies["http"] == "http://127.0.0.1:8080"
        assert proxies["https"] is None
        assert proxies["socks5"] is None
