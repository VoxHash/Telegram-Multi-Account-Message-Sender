"""
Optional AI-assisted copy tools via OpenAI-compatible Chat Completions.

Uses the standard library only (``urllib``) — no OpenAI/Anthropic SDK
dependency. Requires a user-supplied API key (settings / env). Compatible
with OpenAI, and with OpenAI-compatible gateways when ``ai_base_url`` points
at their ``/v1`` prefix.
"""

from __future__ import annotations

import json
import re
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Sequence
from urllib.parse import urljoin

from app.services.cloud.network import check_network_available, is_network_exception


DEFAULT_BASE_URL = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"
DEFAULT_TIMEOUT_SECONDS = 60.0

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
    """Connection settings for an OpenAI-compatible chat endpoint."""

    api_key: str
    base_url: str = DEFAULT_BASE_URL
    model: str = DEFAULT_MODEL
    timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS


def _normalize_base_url(base_url: str) -> str:
    url = (base_url or DEFAULT_BASE_URL).strip().rstrip("/")
    if not url:
        return DEFAULT_BASE_URL
    return url


def _strip_code_fence(text: str) -> str:
    cleaned = text.strip()
    fence = re.match(r"^```(?:json|text|markdown)?\s*\n?(.*?)\n?```$", cleaned, re.DOTALL | re.IGNORECASE)
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


class AICopyService:
    """
    Call an OpenAI-compatible Chat Completions API for campaign copy helpers.

    Instantiate with an explicit ``AICopyConfig``, or omit it to load from
    application settings / environment (``AI_API_KEY``, ``AI_BASE_URL``,
    ``AI_MODEL``).
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
        self._network_check = network_check or (lambda: check_network_available())

    @classmethod
    def from_settings(cls) -> "AICopyService":
        """Build a service from current application settings."""
        from app.services.settings import get_settings

        settings = get_settings()
        api_key = (settings.ai_api_key or "").strip()
        if not api_key:
            return cls(config=None)
        return cls(
            config=AICopyConfig(
                api_key=api_key,
                base_url=_normalize_base_url(settings.ai_base_url),
                model=(settings.ai_model or DEFAULT_MODEL).strip() or DEFAULT_MODEL,
            )
        )

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
            return self._config
        from app.services.settings import get_settings

        settings = get_settings()
        api_key = (settings.ai_api_key or "").strip()
        if not api_key:
            return None
        return AICopyConfig(
            api_key=api_key,
            base_url=_normalize_base_url(settings.ai_base_url),
            model=(settings.ai_model or DEFAULT_MODEL).strip() or DEFAULT_MODEL,
        )

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

        endpoint = urljoin(config.base_url.rstrip("/") + "/", "chat/completions")
        payload: Dict[str, Any] = {
            "model": config.model,
            "temperature": 0.7,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        }
        body = json.dumps(payload).encode("utf-8")
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
            "User-Agent": "telegram-multi-account-sender-ai-copy/1.0",
        }
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

        content = self._extract_message_content(data)
        if not content:
            raise AICopyError("AI provider returned an empty completion")
        return _strip_code_fence(content)

    @staticmethod
    def _extract_message_content(data: Dict[str, Any]) -> str:
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
                parts: List[str] = []
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
