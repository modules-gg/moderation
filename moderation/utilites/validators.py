"""Input validation utilities for the moderation module.

This module provides validation functions for Discord IDs, URLs,
invite codes, and other common input patterns used in moderation
commands and services.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------
SNOWFLAKE_PATTERN: re.Pattern[str] = re.compile(r"^\d{17,20}$")

# Discord invite patterns
DISCORD_INVITE_PATTERNS: list[re.Pattern[str]] = [
    re.compile(r"^(https?://)?(www\.)?(discord\.gg|discordapp\.com/invite)/([a-zA-Z0-9-]+)$"),
    re.compile(r"^([a-zA-Z0-9-]{2,32})$"),  # Bare invite code
]

# URL pattern
URL_PATTERN: re.Pattern[str] = re.compile(
    r"^(https?://)?"  # Protocol
    r"([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}"  # Domain
    r"(/[a-zA-Z0-9._~:/?#[\]@!$&'()*+,;=%-]*)?$",  # Path
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Validators
# ---------------------------------------------------------------------------
def is_valid_snowflake(value: str | int) -> bool:
    """Check if a value is a valid Discord snowflake ID.

    Discord snowflakes are 17-20 digit unsigned integers.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a valid snowflake, False otherwise.

    Example:
        >>> is_valid_snowflake("123456789012345678")
        True
        >>> is_valid_snowflake("abc123")
        False

    """
    if isinstance(value, int):
        value = str(value)

    if not isinstance(value, str):
        return False

    return bool(SNOWFLAKE_PATTERN.match(value))


def is_valid_invite(value: str) -> bool:
    """Check if a value is a valid Discord invite code or URL.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a valid invite, False otherwise.

    Example:
        >>> is_valid_invite("https://discord.gg/abc123")
        True
        >>> is_valid_invite("abc123")
        True
        >>> is_valid_invite("not-an-invite")
        False

    """
    if not value or not isinstance(value, str):
        return False

    for pattern in DISCORD_INVITE_PATTERNS:
        if pattern.match(value.strip()):
            return True

    return False


def is_valid_url(value: str) -> bool:
    """Check if a value is a valid URL.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a valid URL, False otherwise.

    Example:
        >>> is_valid_url("https://example.com/path")
        True
        >>> is_valid_url("not-a-url")
        False

    """
    if not value or not isinstance(value, str):
        return False

    return bool(URL_PATTERN.match(value.strip()))


def is_valid_hex_color(value: str) -> bool:
    """Check if a value is a valid hex color code.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a valid hex color, False otherwise.

    Example:
        >>> is_valid_hex_color("#FF5733")
        True
        >>> is_valid_hex_color("FF5733")
        True
        >>> is_valid_hex_color("not-a-color")
        False

    """
    if not value or not isinstance(value, str):
        return False

    value = value.strip().lstrip("#")
    return len(value) == 6 and all(c in "0123456789ABCDEFabcdef" for c in value)


def is_valid_username(value: str) -> bool:
    """Check if a value is a valid Discord username.

    Discord usernames (new system) are 2-32 characters.
    Legacy discriminators are handled separately.

    Args:
        value: The value to validate.

    Returns:
        True if the value is a valid username, False otherwise.

    """
    if not value or not isinstance(value, str):
        return False

    value = value.strip()
    return 2 <= len(value) <= 32


def is_valid_reason(value: str, max_length: int = 512) -> bool:
    """Check if a moderation reason is valid.

    Args:
        value: The reason text.
        max_length: The maximum allowed length. Defaults to 512.

    Returns:
        True if the reason is valid, False otherwise.

    """
    if not value or not isinstance(value, str):
        return False

    value = value.strip()
    return 1 <= len(value) <= max_length
