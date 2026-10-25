"""
Optional AI-assisted copy tools via provider presets.

Uses the standard library only (``urllib``) — no OpenAI/Anthropic SDK
dependency. Requires a user-supplied API key (settings / env).

Supported providers:
- ``openai`` — OpenAI-compatible Chat Completions (``/v1/chat/completions``)
- ``azure`` — Azure OpenAI deployment path + ``api-version`` query
- ``anthropic`` — Anthropic Messages API (``/v1/messages`` + version headers)
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import urlencode, urljoin

PROVIDER_OPENAI = "openai"
PROVIDER_AZURE = "azure"
PROVIDER_ANTHROPIC = "anthropic"
SUPPORTED_PROVIDERS = (PROVIDER_OPENAI, PROVIDER_AZURE, PROVIDER_ANTHROPIC)

DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AZURE_BASE_URL = "https://YOUR_RESOURCE.openai.azure.com"
DEFAULT_ANTHROPIC_BASE_URL = "https://api.anthropic.com"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_AZURE_MODEL = "gpt-4o-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-3-5-haiku-latest"
DEFAULT_AZURE_API_VERSION = "2024-06-01"
DEFAULT_ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_TIMEOUT_SECONDS = 60.0
DEFAULT_ANTHROPIC_MAX_TOKENS = 2048

_REWRITE_SYSTEM = (
    "You are a professional copywriter for Telegram campaign messages. "
    "Rewrite the user's message to be clearer and more engaging while "
    "preserving meaning, placeholders like {name}/{email}/{phone}/{company}/"
    "{date}/{time}, and any existing spintax {a|b|c} patterns. "
    "Return only the rewritten message text with no quotes or commentary."
)

_SPINTAX_SYSTEM = (
    "You convert Telegram campaign messages into spintax. "
    "Preserve personalization placeholders {name}, {email}, {phone}, "
    "{company}, {date}, {time} exactly. Add natural alternate phrasings "
    "using {option1|option2|option3} syntax for greetings, verbs, and "
    "closings where it improves variety. Do not nest spintax. "
    "Return only the spintax message text with no quotes or commentary."
)

_VARIATIONS_SYSTEM = (
    "You write short Telegram campaign message variations. "
    "Preserve personalization placeholders {name}, {email}, {phone}, "
    "{company}, {date}, {time}. Return exactly the requested number of "
    "alternatives as a JSON array of strings, with no other text."
)


class AICopyError(Exception):
    """Base error for AI copy operations."""


class AICopyNotConfiguredError(AICopyError):
    """Raised when no user-supplied API key is available."""


class AICopyOfflineError(AICopyError):
    """Raised when the network is unavailable for an AI request."""


@dataclass(frozen=True)
class AICopyConfig:
    """Connection settings for an AI chat endpoint."""

    api_key: str
    provider: str = PROVIDER_OPENAI
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    azure_api_version: str = DEFAULT_AZURE_API_VERSION
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def normalize_provider(provider: Optional[str]) -> str:
    """Normalize a provider preset id; unknown values fall back to openai."""
    value = (provider or PROVIDER_OPENAI).strip().lower()
    if value in ("openai-compatible", "compatible", "open_ai"):
        return PROVIDER_OPENAI
    if value in ("azure_openai", "azure-openai", "aoai"):
        return PROVIDER_AZURE
    if value in ("claude", "messages"):
        return PROVIDER_ANTHROPIC
    if value in SUPPORTED_PROVIDERS:
        return value
    return PROVIDER_OPENAI


def default_base_url_for_provider(provider: str) -> str:
    """Default base URL for a provider preset."""
    normalized = normalize_provider(provider)
    if normalized == PROVIDER_AZURE:
        return DEFAULT_AZURE_BASE_URL
    if normalized == PROVIDER_ANTHROPIC:
        return DEFAULT_ANTHROPIC_BASE_URL
    return DEFAULT_BASE_URL


def default_model_for_provider(provider: str) -> str:
    """Default model / deployment id for a provider preset."""
    normalized = normalize_provider(provider)
    if normalized == PROVIDER_AZURE:
        return DEFAULT_AZURE_MODEL
    if normalized == PROVIDER_ANTHROPIC:
        return DEFAULT_ANTHROPIC_MODEL
    return DEFAULT_MODEL


def _normalize_base_url(base_url: str, provider: str = PROVIDER_OPENAI) -> str:
    fallback = default_base_url_for_provider(provider)
    url = (base_url or fallback).strip().rstrip("/")
    if not url:
        return fallback
    return url


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    fence = re.match(
        r"^```(?:json|text|markdown)?\s*\n?(.*?)\n?```$",
        cleaned,
        re.DOTALL | re.IGNORECASE,
    )
    if fence:
        return fence.group(1).strip()
    return cleaned


def _parse_variations_payload(content: str, expected: int) -> List[str]:
    cleaned = _strip_code_fence(content)
    try:
        parsed: Any = json.loads(cleaned)
    except json.JSONDecodeError:
        # Fall back to line-split when the model ignored JSON instructions.
        lines = [line.strip(" -\t") for line in cleaned.splitlines() if line.strip()]
        variations = [line for line in lines if line]
        if len(variations) >= expected:
            return variations[:expected]
        if variations:
            return variations
        raise AICopyError("AI response did not contain usable message variations") from None

    if isinstance(parsed, dict) and "variations" in parsed:
        parsed = parsed["variations"]
    if not isinstance(parsed, list):
        raise AICopyError("AI response was not a JSON array of variations")
    variations = [str(item).strip() for item in parsed if str(item).strip()]
    if not variations:
        raise AICopyError("AI returned an empty variations list")
    return variations[:expected] if expected > 0 else variations


def _azure_resource_root(base_url: str) -> str:
    """
    Normalize an Azure resource endpoint.

    Accepts:
    - ``https://{resource}.openai.azure.com``
    - ``https://{resource}.openai.azure.com/openai``
    - ``https://{resource}.openai.azure.com/openai/deployments/...``
    """
    url = base_url.rstrip("/")
    lower = url.lower()
    marker = "/openai/deployments/"
    if marker in lower:
        idx = lower.index(marker)
        return url[:idx]
    if lower.endswith("/openai"):
        return url[: -len("/openai")]
    return url


def build_request(
    config: AICopyConfig,
    *,
    system: str,
    user: str,
) -> Tuple[str, Dict[str, str], Dict[str, Any]]:
    """
    Build endpoint URL, headers, and JSON body for the configured provider.

    Returns ``(url, headers, payload)``.
    """
    provider = normalize_provider(config.provider)
    base = _normalize_base_url(config.base_url, provider)
    model = (config.model or default_model_for_provider(provider)).strip() or default_model_for_provider(
        provider
    )
    api_key = config.api_key.strip()

    if provider == PROVIDER_AZURE:
        root = _azure_resource_root(base)
        deployment = urllib.parse.quote(model, safe="")
        version = (config.azure_api_version or DEFAULT_AZURE_API_VERSION).strip() or (
            DEFAULT_AZURE_API_VERSION
        )
        query = urlencode({"api-version": version})
        endpoint = f"{root}/openai/deployments/{deployment}/chat/completions?{query}"
        headers = {
            "Content-Type": "application/json",
            "api-key": api_key,
            "User-Agent": "telegram-multi-account-sender-ai-copy/1.0",
        }
        payload: Dict[str, Any] = {
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        return endpoint, headers, payload

    if provider == PROVIDER_ANTHROPIC:
        # Accept either https://api.anthropic.com or .../v1
        if base.lower().endswith("/v1"):
            endpoint = urljoin(base.rstrip("/") + "/", "messages")
        else:
            endpoint = urljoin(base.rstrip("/") + "/", "v1/messages")
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": DEFAULT_ANTHROPIC_VERSION,
            "User-Agent": "telegram-multi-account-sender-ai-copy/1.0",
        }
        payload = {
            "model": model,
            "max_tokens": DEFAULT_ANTHROPIC_MAX_TOKENS,
            "temperature": 0.7,
            "system": system,
            "messages": [{"role": "user", "content": user}],
        }
        return endpoint, headers, payload

    # OpenAI-compatible Chat Completions
    endpoint = urljoin(base.rstrip("/") + "/", "chat/completions")
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "User-Agent": "telegram-multi-account-sender-ai-copy/1.0",
    }
    payload = {
        "model": model,
        "temperature": 0.7,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    return endpoint, headers, payload


def _config_from_settings(settings: Any) -> Optional[AICopyConfig]:
    api_key = (getattr(settings, "ai_api_key", None) or "").strip()
    if not api_key:
        return None
    provider = normalize_provider(getattr(settings, "ai_provider", None))
    return AICopyConfig(
        api_key=api_key,
        provider=provider,
        base_url=_normalize_base_url(getattr(settings, "ai_base_url", "") or "", provider),
        model=(getattr(settings, "ai_model", None) or default_model_for_provider(provider)).strip()
        or default_model_for_provider(provider),
        azure_api_version=(
            getattr(settings, "ai_azure_api_version", None) or DEFAULT_AZURE_API_VERSION
        ).strip()
        or DEFAULT_AZURE_API_VERSION,
    )


class AICopyService:
    """
    Call a configured AI chat API for campaign copy helpers.

    Instantiate with an explicit ``AICopyConfig``, or omit it to load from
    application settings / environment (``AI_PROVIDER``, ``AI_API_KEY``,
    ``AI_BASE_URL``, ``AI_MODEL``, ``AI_AZURE_API_VERSION``).
    """

    def __init__(
        self,
        config: Optional[AICopyConfig] = None,
        *,
        urlopen: Optional[Callable[..., Any]] = None,
        network_check: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._config = config
        self._urlopen = urlopen or urllib.request.urlopen
        if network_check is not None:
            self._network_check = network_check
        else:

            def _default_network_check() -> bool:
                from app.services.cloud.network import check_network_available

                return check_network_available()

            self._network_check = _default_network_check

    @classmethod
    def from_settings(cls) -> "AICopyService":
        """Build a service from current application settings."""
        from app.services.settings import get_settings

        settings = get_settings()
        config = _config_from_settings(settings)
        return cls(config=config)

    def is_configured(self) -> bool:
        """True when a non-empty user API key is available."""
        return self._resolve_config() is not None

    def rewrite(self, text: str, instruction: Optional[str] = None) -> str:
        """Rewrite campaign copy; preserve placeholders and existing spintax."""
        source = (text or "").strip()
        if not source:
            raise AICopyError("Message text is required for AI rewrite")
        user_prompt = source
        if instruction and instruction.strip():
            user_prompt = f"Extra guidance: {instruction.strip()}\n\nMessage:\n{source}"
        return self._complete(system=_REWRITE_SYSTEM, user=user_prompt)

    def to_spintax(self, text: str) -> str:
        """Convert plain (or lightly spun) copy into spintax variations."""
        source = (text or "").strip()
        if not source:
            raise AICopyError("Message text is required for AI spintax conversion")
        return self._complete(system=_SPINTAX_SYSTEM, user=source)

    def suggest_variations(self, text: str, count: int = 3) -> List[str]:
        """Return alternative message drafts as a list of strings."""
        source = (text or "").strip()
        if not source:
            raise AICopyError("Message text is required for AI variations")
        if count < 1 or count > 10:
            raise AICopyError("Variation count must be between 1 and 10")
        user = f"Produce {count} alternatives for this message:\n\n{source}"
        content = self._complete(system=_VARIATIONS_SYSTEM, user=user)
        return _parse_variations_payload(content, expected=count)

    def _resolve_config(self) -> Optional[AICopyConfig]:
        if self._config is not None:
            if not self._config.api_key.strip():
                return None
            # Re-normalize provider in case an older frozen config used aliases.
            if normalize_provider(self._config.provider) != self._config.provider:
                return AICopyConfig(
                    api_key=self._config.api_key,
                    provider=normalize_provider(self._config.provider),
                    base_url=self._config.base_url,
                    model=self._config.model,
                    azure_api_version=self._config.azure_api_version,
                    timeout_seconds=self._config.timeout_seconds,
                )
            return self._config
        from app.services.settings import get_settings

        return _config_from_settings(get_settings())

    def _complete(self, *, system: str, user: str) -> str:
        config = self._resolve_config()
        if config is None:
            raise AICopyNotConfiguredError(
                "AI copy tools need a user-supplied API key. "
                "Set AI_API_KEY in .env or Settings → AI Copy Tools, then try again."
            )
        if not self._network_check():
            raise AICopyOfflineError(
                "Cannot reach the AI provider while offline. "
                "Check your internet connection and try again."
            )

        endpoint, headers, payload = build_request(config, system=system, user=user)
        body = json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(endpoint, data=body, headers=headers, method="POST")
        try:
            with self._urlopen(request, timeout=config.timeout_seconds) as response:
                raw = response.read().decode("utf-8")
                status = getattr(response, "status", None) or response.getcode()
        except urllib.error.HTTPError as exc:
            detail = ""
            try:
                detail = exc.read().decode("utf-8", errors="replace")
            except Exception:
                detail = str(exc)
            raise AICopyError(f"AI provider HTTP {exc.code}: {detail[:500]}") from exc
        except Exception as exc:
            from app.services.cloud.network import is_network_exception

            if is_network_exception(exc):
                raise AICopyOfflineError(
                    "Cannot reach the AI provider (network error). "
                    "Check connectivity, VPN/firewall, and AI_BASE_URL."
                ) from exc
            raise AICopyError(f"AI request failed: {exc}") from exc

        if status is not None and int(status) >= 400:
            raise AICopyError(f"AI provider HTTP {status}: {raw[:500]}")

        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AICopyError("AI provider returned invalid JSON") from exc

        content = self._extract_message_content(data, normalize_provider(config.provider))
        if not content:
            raise AICopyError("AI provider returned an empty completion")
        return _strip_code_fence(content)

    @staticmethod
    def _extract_message_content(data: Dict[str, Any], provider: str = PROVIDER_OPENAI) -> str:
        if provider == PROVIDER_ANTHROPIC:
            blocks: Sequence[Any] = data.get("content") or []
            parts: List[str] = []
            for block in blocks:
                if isinstance(block, dict) and block.get("type") == "text":
                    parts.append(str(block.get("text", "")))
                elif isinstance(block, str):
                    parts.append(block)
            return "\n".join(p for p in parts if p).strip()

        choices: Sequence[Any] = data.get("choices") or []
        if not choices:
            return ""
        first = choices[0]
        if not isinstance(first, dict):
            return ""
        message = first.get("message") or {}
        if isinstance(message, dict):
            content = message.get("content")
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):
                parts = []
                for part in content:
                    if isinstance(part, dict) and part.get("type") == "text":
                        parts.append(str(part.get("text", "")))
                    elif isinstance(part, str):
                        parts.append(part)
                return "\n".join(p for p in parts if p).strip()
        text = first.get("text")
        return str(text).strip() if text else ""


def get_ai_copy_service() -> AICopyService:
    """Factory that reads the current settings snapshot."""
    return AICopyService.from_settings()
