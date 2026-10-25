"""Ensure AI Copy Tools UI keys exist in every bundled locale (not English-only)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

TRANSLATIONS_DIR = Path(__file__).resolve().parents[2] / "app" / "translations"

AI_TEMPLATE_KEYS = (
    "ai_rewrite",
    "ai_rewrite_tooltip",
    "ai_to_spintax",
    "ai_to_spintax_tooltip",
    "ai_variations",
    "ai_variations_tooltip",
    "ai_not_configured_title",
    "ai_not_configured_message",
    "ai_success_title",
    "ai_rewrite_done",
    "ai_spintax_done",
    "ai_variations_pick",
    "ai_use_first_variation",
    "ai_offline_title",
    "ai_failed",
)

AI_SETTINGS_KEYS = (
    "ai_copy_settings",
    "ai_provider",
    "ai_provider_openai",
    "ai_provider_azure",
    "ai_provider_anthropic",
    "ai_api_key",
    "ai_api_key_placeholder",
    "ai_base_url",
    "ai_model",
    "ai_model_deployment",
    "ai_azure_api_version",
    "ai_copy_help",
)

EXPECTED_LOCALES = (
    "en",
    "fr",
    "es",
    "zh",
    "ja",
    "de",
    "ru",
    "pt",
    "ko",
    "ca",
    "eu",
    "gl",
    "et",
)


def _load(lang: str) -> dict:
    path = TRANSLATIONS_DIR / f"{lang}.json"
    assert path.is_file(), f"missing translation file: {path}"
    return json.loads(path.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def english() -> dict:
    return _load("en")


@pytest.mark.parametrize("lang", EXPECTED_LOCALES)
def test_ai_template_keys_present(lang: str, english: dict) -> None:
    data = _load(lang)
    templates = data["templates"]
    for key in AI_TEMPLATE_KEYS:
        assert key in templates, f"{lang}: missing templates.{key}"
        value = templates[key]
        assert isinstance(value, str) and value.strip(), f"{lang}: empty templates.{key}"
        assert "{error}" in templates["ai_failed"]
    if lang != "en":
        # Localized titles must not fall back to the English kit verbatim.
        assert templates["ai_rewrite"] != english["templates"]["ai_rewrite"]
        assert (
            templates["ai_not_configured_title"]
            != english["templates"]["ai_not_configured_title"]
        )


@pytest.mark.parametrize("lang", EXPECTED_LOCALES)
def test_ai_settings_keys_present(lang: str, english: dict) -> None:
    data = _load(lang)
    settings = data["settings"]
    for key in AI_SETTINGS_KEYS:
        assert key in settings, f"{lang}: missing settings.{key}"
        value = settings[key]
        assert isinstance(value, str) and value.strip(), f"{lang}: empty settings.{key}"
    if lang != "en":
        assert settings["ai_copy_settings"] != english["settings"]["ai_copy_settings"]


def test_all_expected_locale_files_exist() -> None:
    found = {p.stem for p in TRANSLATIONS_DIR.glob("*.json")}
    assert set(EXPECTED_LOCALES) <= found
