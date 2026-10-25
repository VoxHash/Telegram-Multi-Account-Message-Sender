"""
Unit tests for optional AI-assisted copy tools (stdlib HTTP, no SDK).
"""

from __future__ import annotations

import io
import json
from typing import Any, Dict
from unittest.mock import MagicMock

import pytest

from app.services.ai_copy import (
    DEFAULT_ANTHROPIC_BASE_URL,
    DEFAULT_ANTHROPIC_VERSION,
    DEFAULT_AZURE_API_VERSION,
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    PROVIDER_ANTHROPIC,
    PROVIDER_AZURE,
    PROVIDER_OPENAI,
    AICopyConfig,
    AICopyError,
    AICopyNotConfiguredError,
    AICopyOfflineError,
    AICopyService,
    _parse_variations_payload,
    build_request,
    get_ai_copy_service,
    normalize_provider,
)


class _FakeHTTPResponse:
    def __init__(self, payload: Dict[str, Any], status: int = 200) -> None:
        self._raw = json.dumps(payload).encode("utf-8")
        self.status = status

    def read(self) -> bytes:
        return self._raw

    def getcode(self) -> int:
        return self.status

    def __enter__(self) -> "_FakeHTTPResponse":
        return self

    def __exit__(self, *args: Any) -> None:
        return None


def _completion_payload(content: str) -> Dict[str, Any]:
    return {
        "id": "chatcmpl-test",
        "choices": [{"message": {"role": "assistant", "content": content}}],
    }


def _anthropic_payload(content: str) -> Dict[str, Any]:
    return {
        "id": "msg_test",
        "type": "message",
        "role": "assistant",
        "content": [{"type": "text", "text": content}],
    }


@pytest.fixture
def configured_service():
    calls: list[Any] = []

    def fake_urlopen(request: Any, timeout: float = 60.0) -> _FakeHTTPResponse:
        calls.append((request, timeout))
        body = json.loads(request.data.decode("utf-8"))
        user = body["messages"][-1]["content"]
        system = body["messages"][0]["content"]
        if "JSON array of strings" in system:
            content = json.dumps(["Hi {name}", "Hello {name}", "Hey {name}"])
        elif "convert Telegram campaign messages into spintax" in system:
            content = "Hello {friend|buddy}, welcome to {our team|our service}!"
        else:
            content = f"Rewritten: {user.split('Message:')[-1].strip() or user}"
        return _FakeHTTPResponse(_completion_payload(content))

    service = AICopyService(
        config=AICopyConfig(api_key="sk-test-key", model="gpt-4o-mini"),
        urlopen=fake_urlopen,
        network_check=lambda: True,
    )
    service._test_calls = calls  # type: ignore[attr-defined]
    return service


class TestAICopyConfigGuards:
    def test_not_configured_without_key(self):
        service = AICopyService(config=None, network_check=lambda: True)
        assert service.is_configured() is False
        with pytest.raises(AICopyNotConfiguredError):
            service.rewrite("Hello {name}")

    def test_empty_key_config_is_not_configured(self):
        service = AICopyService(
            config=AICopyConfig(api_key="   "),
            network_check=lambda: True,
        )
        assert service.is_configured() is False

    def test_offline_raises_before_http(self):
        urlopen = MagicMock()
        service = AICopyService(
            config=AICopyConfig(api_key="sk-test"),
            urlopen=urlopen,
            network_check=lambda: False,
        )
        with pytest.raises(AICopyOfflineError):
            service.rewrite("Hello")
        urlopen.assert_not_called()

    def test_empty_text_rejected(self, configured_service):
        with pytest.raises(AICopyError):
            configured_service.rewrite("  ")
        with pytest.raises(AICopyError):
            configured_service.to_spintax("")
        with pytest.raises(AICopyError):
            configured_service.suggest_variations("\n")


class TestAICopyOperations:
    def test_rewrite_sends_bearer_and_returns_text(self, configured_service):
        result = configured_service.rewrite("Hello {name}")
        assert "Hello {name}" in result
        request, timeout = configured_service._test_calls[0]
        assert timeout == 60.0
        assert request.get_header("Authorization") == "Bearer sk-test-key"
        assert request.full_url == f"{DEFAULT_BASE_URL}/chat/completions"
        body = json.loads(request.data.decode("utf-8"))
        assert body["model"] == DEFAULT_MODEL
        assert body["messages"][0]["role"] == "system"

    def test_to_spintax(self, configured_service):
        result = configured_service.to_spintax("Hello friend, welcome to our team!")
        assert "{" in result and "|" in result

    def test_suggest_variations(self, configured_service):
        variations = configured_service.suggest_variations("Hello {name}", count=3)
        assert len(variations) == 3
        assert all("{name}" in item for item in variations)

    def test_http_error_mapped(self):
        import urllib.error

        def boom(request: Any, timeout: float = 60.0) -> Any:
            raise urllib.error.HTTPError(
                request.full_url,
                401,
                "Unauthorized",
                hdrs=None,
                fp=io.BytesIO(b'{"error":"bad key"}'),
            )

        service = AICopyService(
            config=AICopyConfig(api_key="sk-bad"),
            urlopen=boom,
            network_check=lambda: True,
        )
        with pytest.raises(AICopyError) as exc_info:
            service.rewrite("Hello")
        assert "401" in str(exc_info.value)


class TestVariationParsing:
    def test_parse_json_array(self):
        assert _parse_variations_payload('["a", "b", "c"]', expected=2) == ["a", "b"]

    def test_parse_fenced_json(self):
        payload = '```json\n["one", "two"]\n```'
        assert _parse_variations_payload(payload, expected=2) == ["one", "two"]

    def test_parse_line_fallback(self):
        payload = "- alpha\n- beta\n- gamma"
        assert _parse_variations_payload(payload, expected=3) == ["alpha", "beta", "gamma"]


class TestProviderPresets:
    def test_normalize_provider_aliases(self):
        assert normalize_provider("OpenAI") == PROVIDER_OPENAI
        assert normalize_provider("azure-openai") == PROVIDER_AZURE
        assert normalize_provider("claude") == PROVIDER_ANTHROPIC
        assert normalize_provider("unknown") == PROVIDER_OPENAI

    def test_build_request_openai(self):
        config = AICopyConfig(api_key="sk-test", provider=PROVIDER_OPENAI)
        url, headers, payload = build_request(config, system="sys", user="hi")
        assert url == f"{DEFAULT_BASE_URL}/chat/completions"
        assert headers["Authorization"] == "Bearer sk-test"
        assert payload["model"] == DEFAULT_MODEL
        assert payload["messages"][0]["role"] == "system"

    def test_build_request_azure_path_and_api_version(self):
        config = AICopyConfig(
            api_key="azure-key",
            provider=PROVIDER_AZURE,
            base_url="https://myres.openai.azure.com",
            model="camp-copy",
            azure_api_version="2024-06-01",
        )
        url, headers, payload = build_request(config, system="sys", user="hi")
        assert url.startswith(
            "https://myres.openai.azure.com/openai/deployments/camp-copy/chat/completions?"
        )
        assert "api-version=2024-06-01" in url
        assert headers["api-key"] == "azure-key"
        assert "Authorization" not in headers
        assert "model" not in payload
        assert payload["messages"][1]["content"] == "hi"

    def test_build_request_azure_strips_openai_suffix(self):
        config = AICopyConfig(
            api_key="k",
            provider=PROVIDER_AZURE,
            base_url="https://myres.openai.azure.com/openai",
            model="dep",
        )
        url, _headers, _payload = build_request(config, system="s", user="u")
        assert url.startswith(
            "https://myres.openai.azure.com/openai/deployments/dep/chat/completions?"
        )

    def test_build_request_anthropic_messages(self):
        config = AICopyConfig(
            api_key="anth-key",
            provider=PROVIDER_ANTHROPIC,
            base_url=DEFAULT_ANTHROPIC_BASE_URL,
            model="claude-3-5-haiku-latest",
        )
        url, headers, payload = build_request(config, system="sys", user="hi")
        assert url == f"{DEFAULT_ANTHROPIC_BASE_URL}/v1/messages"
        assert headers["x-api-key"] == "anth-key"
        assert headers["anthropic-version"] == DEFAULT_ANTHROPIC_VERSION
        assert "Authorization" not in headers
        assert payload["system"] == "sys"
        assert payload["messages"] == [{"role": "user", "content": "hi"}]
        assert payload["max_tokens"] >= 1
        assert "model" in payload

    def test_azure_rewrite_sends_api_key_header(self):
        calls: list = []

        def fake_urlopen(request, timeout: float = 60.0):
            calls.append(request)
            return _FakeHTTPResponse(_completion_payload("Azure rewritten"))

        service = AICopyService(
            config=AICopyConfig(
                api_key="azure-key",
                provider=PROVIDER_AZURE,
                base_url="https://demo.openai.azure.com",
                model="my-deploy",
                azure_api_version=DEFAULT_AZURE_API_VERSION,
            ),
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        assert service.rewrite("Hello") == "Azure rewritten"
        req = calls[0]
        assert req.get_header("Api-key") == "azure-key"
        assert "api-version=" in req.full_url
        assert "/openai/deployments/my-deploy/chat/completions" in req.full_url

    def test_anthropic_rewrite_parses_content_blocks(self):
        calls: list = []

        def fake_urlopen(request, timeout: float = 60.0):
            calls.append(request)
            return _FakeHTTPResponse(_anthropic_payload("Claude rewrite"))

        service = AICopyService(
            config=AICopyConfig(
                api_key="anth-key",
                provider=PROVIDER_ANTHROPIC,
                base_url=DEFAULT_ANTHROPIC_BASE_URL,
                model="claude-3-5-haiku-latest",
            ),
            urlopen=fake_urlopen,
            network_check=lambda: True,
        )
        assert service.rewrite("Hello") == "Claude rewrite"
        req = calls[0]
        assert req.get_header("X-api-key") == "anth-key"
        assert req.get_header("Anthropic-version") == DEFAULT_ANTHROPIC_VERSION
        assert req.full_url.endswith("/v1/messages")
        body = json.loads(req.data.decode("utf-8"))
        assert body["system"]
        assert body["messages"][0]["role"] == "user"


class TestSettingsIntegration:
    def test_from_settings_reads_key(self, tmp_path, monkeypatch):
        for key in (
            "AI_PROVIDER",
            "AI_API_KEY",
            "AI_BASE_URL",
            "AI_MODEL",
            "AI_AZURE_API_VERSION",
            "TELEGRAM_API_ID",
            "TELEGRAM_API_HASH",
            "DATABASE_URL",
            "APP_DATA_DIR",
            "SESSIONS_DIR",
            "LOGS_DIR",
            "CONTENT_DIR",
        ):
            monkeypatch.delenv(key, raising=False)

        from app.services.settings import Settings

        settings = Settings(
            app_data_dir=str(tmp_path / "data"),
            sessions_dir=str(tmp_path / "sessions"),
            logs_dir=str(tmp_path / "logs"),
            content_dir=str(tmp_path / "content"),
            database_url=f"sqlite:///{tmp_path / 't.db'}",
            ai_provider="openai",
            ai_api_key="sk-from-settings",
            ai_base_url="https://example.com/v1",
            ai_model="gpt-4o-mini",
        )
        assert settings.is_ai_copy_configured() is True

        monkeypatch.setattr(
            "app.services.settings.get_settings",
            lambda: settings,
        )
        service = AICopyService.from_settings()
        assert service.is_configured() is True

    def test_from_settings_azure_provider(self, tmp_path, monkeypatch):
        for key in (
            "AI_PROVIDER",
            "AI_API_KEY",
            "AI_BASE_URL",
            "AI_MODEL",
            "AI_AZURE_API_VERSION",
        ):
            monkeypatch.delenv(key, raising=False)

        from app.services.settings import Settings

        settings = Settings(
            app_data_dir=str(tmp_path / "data"),
            sessions_dir=str(tmp_path / "sessions"),
            logs_dir=str(tmp_path / "logs"),
            content_dir=str(tmp_path / "content"),
            database_url=f"sqlite:///{tmp_path / 't.db'}",
            ai_provider="azure",
            ai_api_key="azure-key",
            ai_base_url="https://demo.openai.azure.com",
            ai_model="camp-deploy",
            ai_azure_api_version="2024-06-01",
        )
        assert settings.ai_provider == PROVIDER_AZURE
        monkeypatch.setattr("app.services.settings.get_settings", lambda: settings)
        service = AICopyService.from_settings()
        config = service._resolve_config()
        assert config is not None
        assert config.provider == PROVIDER_AZURE
        assert config.azure_api_version == "2024-06-01"

    def test_get_ai_copy_service_without_key(self, tmp_path, monkeypatch):
        for key in ("AI_PROVIDER", "AI_API_KEY", "AI_BASE_URL", "AI_MODEL"):
            monkeypatch.delenv(key, raising=False)

        from app.services.settings import Settings

        settings = Settings(
            app_data_dir=str(tmp_path / "data"),
            sessions_dir=str(tmp_path / "sessions"),
            logs_dir=str(tmp_path / "logs"),
            content_dir=str(tmp_path / "content"),
            database_url=f"sqlite:///{tmp_path / 't.db'}",
            ai_api_key=None,
        )
        monkeypatch.setattr("app.services.settings.get_settings", lambda: settings)
        service = get_ai_copy_service()
        assert service.is_configured() is False
        assert settings.is_ai_copy_configured() is False
