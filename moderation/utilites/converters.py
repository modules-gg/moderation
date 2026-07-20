"""Input conversion utilities for the moderation module.

This module provides functions for parsing user input into structured
data types. Converters handle duration strings, mentions, IDs, and
other Discord-specific input formats.

"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING

from moderation.constants import TIME_UNIT_MULTIPLIERS
from moderation.exceptions.commands import InvalidDurationError

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Duration Parsing
# ---------------------------------------------------------------------------
DURATION_PATTERN: re.Pattern[str] = re.compile(
    r"^(\d+[smhdw])+$",
    re.IGNORECASE,
)


def parse_duration(duration_str: str) -> int:
    """Parse a human-readable duration string into seconds.

    Supports compound durations like ``1h30m``, ``2d12h``, ``1w3d``.
    Single-unit durations like ``45s``, ``5m``, ``2h`` are also valid.

    Args:
        duration_str: The duration string to parse.

    Returns:
        The total duration in seconds.

    Raises:
        InvalidDurationError: If the string cannot be parsed or is invalid.

    Example:
        >>> parse_duration("1h30m")
        5400
        >>> parse_duration("2d")
        172800

    """
    if not duration_str or not duration_str.strip():
        raise InvalidDurationError(
            "Duration cannot be empty.",
            input_value=duration_str,
        )

    duration_str = duration_str.strip().lower()
    total_seconds = 0
    current_number = ""
    idx = 0

    while idx < len(duration_str):
        char = duration_str[idx]

        if char.isdigit():
            current_number += char
            idx += 1
            continue

        if char.isalpha():
            if not current_number:
                raise InvalidDurationError(
                    f"Invalid duration format: '{duration_str}'. "
                    "Numbers must precede time units.",
                    input_value=duration_str,
                )

            # Collect the full unit word
            unit_start = idx
            while idx < len(duration_str) and duration_str[idx].isalpha():
                idx += 1
            unit = duration_str[unit_start:idx]

            multiplier = TIME_UNIT_MULTIPLIERS.get(unit)
            if multiplier is None:
                valid_units = ", ".join(sorted(set(TIME_UNIT_MULTIPLIERS.keys())))
                raise InvalidDurationError(
                    f"Unknown time unit: '{unit}'. "
                    f"Supported units: {valid_units}.",
                    input_value=duration_str,
                )

            total_seconds += int(current_number) * multiplier
            current_number = ""
            continue

        # Skip whitespace
        if char.isspace():
            idx += 1
            continue

        raise InvalidDurationError(
            f"Invalid character in duration: '{char}'.",
            input_value=duration_str,
        )

    if current_number:
        # Trailing number without unit — treat as seconds
        total_seconds += int(current_number)

    if total_seconds <= 0:
        raise InvalidDurationError(
            "Duration must be greater than zero.",
            input_value=duration_str,
        )

    return total_seconds


def format_duration(seconds: int) -> str:
    """Format a duration in seconds into a human-readable string.

    Args:
        seconds: The duration in seconds.

    Returns:
        A human-readable duration string.

    Example:
        >>> format_duration(5400)
        '1h 30m'
        >>> format_duration(90061)
        '1d 1h 1m 1s'

    """
    if seconds <= 0:
        return "0s"

    parts = []
    remaining = seconds

    for unit, multiplier in [
        ("d", 86400),
        ("h", 3600),
        ("m", 60),
        ("s", 1),
    ]:
        if remaining >= multiplier:
:
            count = remaining // multiplier
            parts            count = remaining // multiplier
            parts.append(f"{count}{unit}")
            remaining %= multiplier

    return " ".join(parts) if parts else "0s"


# ---------------------------------------------------------------------------
# Mention Parsing
# ---------------------------------------------------------------------------
USER_MENTION_PATTERN: re.Pattern[str] = re.compile(r"^<@!?(\d{17,20})>$")
CHANNEL_MENTION_PATTERN: re.Pattern[str] = re.compile(r"^<#(\d{17,20})>$")
ROLE_MENTION_PATTERN: re.Pattern[str] = re.compile(r"^<@&(\d{17,20})>$")


def parse_user_mention(text: str) -> int | None:
    """Parse a Discord user mention or raw ID into a user ID.

    Args:
        text: The text to parse (e.g., ``@username``, ``<@123456789>``, ``123456789``).

    Returns:
        The user ID as an integer, or None if parsing fails.

    """
    text = text.strip()

    # Check for mention format
    match = USER_MENTION_PATTERN.match(text)
    if match:
        return int(match.group(1))

    # Check for raw ID
    if text.isdigit() and len(text) >= 17:
        return int(text)

    return None


def parse_channel_mention(text: str) -> int | None:
    """Parse a Discord channel mention or raw ID into a channel ID.

    Args:
        text: The text to parse (e.g., ``#general``, ``<#123456789>``, ``123456789``).

    Returns:
        The channel ID as an integer, or None if parsing fails.

    """
    text = text.strip()

    match = CHANNEL_MENTION_PATTERN.match(text)
    if match:
        return int(match.group(1))

    if text.isdigit() and len(text) >= 17:
        return int(text)

    return None


def parse_role_mention(text: str) -> int | None:
    """Parse a Discord role mention or raw ID into a role ID.

    Args:
        text: The text to parse (e.g., ``@RoleName``, ``<@&123456789>``, ``123456789``).

    Returns:
        The role ID as an integer, or None if parsing fails.

    """
    text = text.strip()

    match = ROLE_MENTION_PATTERN.match(text)
    if match:
        return int(match.group(1))

    if text.isdigit() and len(text) >= 17:
        return int(text)

    return None
