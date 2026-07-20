"""Utility functions and helpers for the moderation module.

This package contains reusable utility functions for formatting,
conversions, validators, and other common operations used across
the codebase.

"""

from __future__ import annotations

from moderation.utilities.converters import (
    parse_duration,
    format_duration,
    parse_user_mention,
    parse_channel_mention,
    parse_role_mention,
)
from moderation.utilities.formatters import (
    truncate,
    pluralize,
    codeblock,
    timestamp,
    mention_user,
    mention_channel,
    mention_role,
)
from moderation.utilities.validators import (
    is_valid_snowflake,
    is_valid_invite,
    is_valid_url,
)

__all__ = [
    # Converters
    "parse_duration",
    "format_duration",
    "parse_user_mention",
    "parse_channel_mention",
    "parse_role_mention",
    # Formatters
    "truncate",
    "pluralize",
    "codeblock",
    "timestamp",
    "mention_user",
    "mention_channel",
    "mention_role",
    # Validators
    "is_valid_snowflake",
    "is_valid_invite",
    "is_valid_url",
]
