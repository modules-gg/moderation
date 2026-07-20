"""Internationalization (i18n) support for the moderation module.

This package provides localization capabilities for bot responses,
allowing messages to be displayed in different languages based on
guild or user preferences.

Version 1.2 will expand this to full locale support with JSON/MO files.
For now, a default English string catalog is provided.

"""

from __future__ import annotations

from moderation.localization.strings import (
    get_string,
    get_string_f,
    DEFAULT_LOCALE,
    SUPPORTED_LOCALES,
)

__all__ = [
    "get_string",
    "get_string_f",
    "DEFAULT_LOCALE",
    "SUPPORTED_LOCALES",
]
