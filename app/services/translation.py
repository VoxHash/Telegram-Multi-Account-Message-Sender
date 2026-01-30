"""
Translation management for multi-language support.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional
from PyQt5.QtCore import QObject, pyqtSignal

from .settings import Language, get_settings


class TranslationManager(QObject):
    """Manages application translations."""
    
    # Signal emitted when language changes
    language_changed = pyqtSignal(str)
    
    def __init__(self, settings=None):
        super().__init__()
        self.settings = settings or get_settings()
        self.current_language = self.settings.language.value
        self.translations: Dict[str, Dict[str, str]] = {}
        self.load_translations()
    
    def load_translations(self):
        """Load all translation files."""
        translations_dir = Path(__file__).parent.parent / "translations"
        
        for language in Language:
            lang_code = language.value
            translation_file = translations_dir / f"{lang_code}.json"
            
            if translation_file.exists():
                try:
                    with open(translation_file, 'r', encoding='utf-8') as f:
                        self.translations[lang_code] = json.load(f)
                    print(f"Loaded translations for {lang_code}")
                except Exception as e:
                    print(f"Error loading translation for {lang_code}: {e}")
                    self.translations[lang_code] = {}
            else:
                print(f"Translation file not found for {lang_code}: {translation_file}")
                self.translations[lang_code] = {}
    
    def get_text(self, key: str, **kwargs) -> str:
        """Get translated text for a key."""
        # Get translation for current language
        translation = self.translations.get(self.current_language, {})
        
        # Handle nested keys (e.g., "tabs.accounts")
        text = translation
        for part in key.split('.'):
            if isinstance(text, dict) and part in text:
                text = text[part]
            else:
                # If key not found, return the key itself
                print(f"Translation key not found: {key} (language: {self.current_language})")
                return key
        
        # Ensure text is a string
        text = str(text) if text is not None else key
        
        # Format with kwargs if provided
        if kwargs:
            try:
                text = text.format(**kwargs)
            except (KeyError, ValueError):
                pass
        
        return text
    
    def set_language(self, language: str):
        """Set the current language."""
        if language in [lang.value for lang in Language]:
            self.current_language = language
            # Reload translations for the new language
            self.load_translations()
            self.language_changed.emit(language)
    
    def get_available_languages(self) -> Dict[str, str]:
        """Get available languages with their display names."""
        return {
            "en": "English",
            "fr": "Français",
            "es": "Español",
            "zh": "中文",
            "ja": "日本語",
            "de": "Deutsch",
            "ru": "Русский",
            "et": "Eesti",
            "pt": "Português",
            "ko": "한국어",
            "ca": "Català",
            "eu": "Euskera",
            "gl": "Galego"
        }
    
    def get_language_display_name(self, lang_code: str) -> str:
        """Get display name for a language code."""
        languages = self.get_available_languages()
        return languages.get(lang_code, lang_code.upper())


# Global translation manager instance
_translation_manager: Optional[TranslationManager] = None


def get_translation_manager() -> TranslationManager:
    """Get the global translation manager instance."""
    global _translation_manager
    if _translation_manager is None:
        _translation_manager = TranslationManager()
    return _translation_manager


def _(key: str, **kwargs) -> str:
    """Convenience function for getting translated text."""
    return get_translation_manager().get_text(key, **kwargs)
