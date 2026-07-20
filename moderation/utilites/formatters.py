"""String formatting utilities for the moderation module.

This module provides helper functions for formatting text, mentions,
timestamps, and other Discord-specific output. These utilities ensure
consistent formatting across all bot responses and logs.

"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Text Formatting
# ---------------------------------------------------------------------------
def truncate(text: str, max_length: int, suffix: str = "…") -> str:
    """Truncate a string to a maximum length.

    Args:
        text: The text to truncate.
        max_length: The maximum allowed length.
        suffix: The suffix to append when truncating. Defaults to "…".

    Returns:
        The truncated string, or the original if it fits.

    Example:
        >>> truncate("This is a very long message", 15)
        'This is a very…'

    """
    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def pluralize(count: int, singular: str, plural: str | None = None) -> str:
    """Return the appropriate singular or plural form.

    Args:
        count: The quantity.
        singular: The singular form of the word.
        plural: The plural form. If None, appends "s" to singular.

    Returns:
        The appropriately pluralized string including the count.

    Example:
        >>> pluralize(1, "member")
        '1 member'
        >>> pluralize(5, "member")
        '5 members'

    """
    if plural is None:
        plural = singular + "s"

    if count == 1:
        return f"{count} {singular}"
    return f"{count} {plural}"


def codeblock(content: str, language: str | None = None) -> str:
    """Wrap content in a Discord code block.

    Args:
        content: The content to wrap.
        language: The syntax highlighting language. Defaults to plain text.

    Returns:
        The formatted code block string.

    Example:
        >>> codeblock("print('hello')", "python")
        "```python\\nprint('hello')\\n```"

    """
    if language:
        return f"```{language}\n{content}\n```"
    return f"```\n{content}\n```"


# ---------------------------------------------------------------------------
# Timestamp Formatting
# ---------------------------------------------------------------------------
def timestamp(dt: datetime | None = None, style: str = "f") -> str:
    """Format a datetime as a Discord timestamp.

    Args:
        dt: The datetime to format. Defaults to now (UTC).
        style: The Discord timestamp style:
            - "t" → Short time (16:20)
            - "T" → Long time (16:20:30)
            - "d" → Short date (20/07/2026)
            - "D" → Long date (20 July 2026)
            - "f" → Short datetime (20 July 2026 16:20) [default]
            - "F" → Long datetime (Tuesday, 20 July 2026 16:20)
            - "R" → Relative time (2 hours ago)

    Returns:
        The Discord timestamp markdown string.

    Example:
        >>> timestamp(datetime.now(timezone.utc), "R")
        '<t:1234567890:R>'

    """
    if dt is None:
        dt = datetime.now(timezone.utc)

    unix_timestamp = int(dt.timestamp())
    return f"<t:{unix_timestamp}:{style}>"


def relative_timestamp(dt: datetime) -> str:
    """Format a datetime as a Discord relative timestamp.

    Args:
        dt: The datetime to format.

    Returns:
        The relative Discord timestamp markdown string.

    """
    return timestamp(dt, "R")


# ---------------------------------------------------------------------------
# Mention Formatting
# ---------------------------------------------------------------------------
def mention_user(user_id: int) -> str:
    """Format a user ID as a Discord mention.

    Args:
        user_id: The Discord user ID.

    Returns:
        The user mention string.

    """
    return f"<@{user_id}>"


def mention_channel(channel_id: int) -> str:
    """Format a channel ID as a Discord mention.

    Args:
        channel_id: The Discord channel ID.

    Returns:
        The channel mention string.

    """
    return f"<#{channel_id}>"


def mention_role(role_id: int) -> str:
    """Format a role ID as a Discord mention.

    Args:
        role_id: The Discord role ID.

    Returns:
        The role mention string.

    """
    return f"<@&{role_id}>"


# ---------------------------------------------------------------------------
# Embed Helpers
# ---------------------------------------------------------------------------
def field_safe(text: str, max_length: int = 1024) -> str:
    """Ensure text fits within a Discord embed field value.

    Args:
        text: The text to check.
        max_length: The maximum length. Defaults to 1024.

    Returns:
        The text, truncated if necessary.

    """
    return truncate(text, max_length)


def title_safe(text: str, max_length: int = 256) -> str:
    """Ensure text fits within a Discord embed title.

    Args:
        text: The text to check.
        max_length: The maximum length. Defaults to 256.

    Returns:
        The text, truncated if necessary.

    """
    return truncate(text, max_length)


def description_safe(text: str, max_length: int = 4096) -> str:
    """Ensure text fits within a Discord embed description.

    Args:
        text: The text to check.
        max_length: The maximum length. Defaults to 4096.

    Returns:
        The text, truncated if necessary.

    """
    return truncate(text, max_length)
