"""Application-wide constants and enumerations for the moderation module.

This module defines immutable constants, enums, and lookup tables used
throughout the codebase. Centralizing these values prevents magic
strings and numbers from scattering across the project.

Example:
    Use constants in command implementations::

        from moderation.constants import PermissionLevel, DEFAULT_TIMEOUT_DURATION

        if user_level < PermissionLevel.MODERATOR:
            await ctx.send(Messages.INSUFFICIENT_PERMISSIONS)

"""

from __future__ import annotations

import enum
from typing import Final


# ---------------------------------------------------------------------------
# Version Information
# ---------------------------------------------------------------------------
VERSION: Final[str] = "0.1.0"
VERSION_NAME: Final[str] = "Remake"
MINIMUM_DISCORD_PY_VERSION: Final[str] = "2.3.0"


# ---------------------------------------------------------------------------
# Time Constants
# ---------------------------------------------------------------------------
SECONDS_PER_MINUTE: Final[int] = 60
SECONDS_PER_HOUR: Final[int] = 3600
SECONDS_PER_DAY: Final[int] = 86400
SECONDS_PER_WEEK: Final[int] = 604800
SECONDS_PER_MONTH: Final[int] = 2592000  # 30 days

DEFAULT_TIMEOUT_DURATION: Final[int] = 3600  # 1 hour
MAX_TIMEOUT_DURATION: Final[int] = 2419200  # 28 days (Discord limit)
MIN_TIMEOUT_DURATION: Final[int] = 1  # 1 second


# ---------------------------------------------------------------------------
# Moderation Limits
# ---------------------------------------------------------------------------
MAX_PURGE_MESSAGES: Final[int] = 1000
DEFAULT_PURGE_MESSAGES: Final[int] = 100
MAX_SLOWMODE_DURATION: Final[int] = 21600  # 6 hours (Discord limit)
MIN_SLOWMODE_DURATION: Final[int] = 0  # Disabled


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------
DEFAULT_PAGE_SIZE: Final[int] = 10
MAX_PAGE_SIZE: Final[int] = 25


# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------
DEFAULT_DB_PATH: Final[str] = "data/moderation.db"
MAX_DB_CONNECTIONS: Final[int] = 10
DB_TIMEOUT: Final[float] = 30.0


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------
class PermissionLevel(enum.IntEnum):
    """Hierarchy levels for moderation permissions.

    Higher values indicate greater authority. These levels are used
    to enforce the moderation hierarchy (moderators cannot action
    users with equal or higher permission levels).

    """

    EVERYONE = 0
    HELPER = 1
    TRIAL_MODERATOR = 2
    MODERATOR = 3
    SENIOR_MODERATOR = 4
    ADMINISTRATOR = 5
    OWNER = 6


class CaseType(enum.StrEnum):
    """Types of moderation cases that can be recorded.

    Each case type corresponds to a specific moderation action.

    """

    KICK = "kick"
    BAN = "ban"
    UNBAN = "unban"
    TIMEOUT = "timeout"
    WARN = "warn"
    PURGE = "purge"
    NICKNAME = "nickname"
    LOCK = "lock"
    UNLOCK = "unlock"
    SLOWMODE = "slowmode"
    ROLE_ADD = "role_add"
    ROLE_REMOVE = "role_remove"


class AppealStatus(enum.StrEnum):
    """Status values for moderation case appeals.

    Appeals allow users to contest moderation actions taken against them.

    """

    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    ACCEPTED = "accepted"
    DENIED = "denied"
    ESCALATED = "escalated"
    WITHDRAWN = "withdrawn"


class LogLevel(enum.StrEnum):
    """Structured log level identifiers for the moderation module.

    These map to standard Python logging levels but provide a
    type-safe interface for configuration and filtering.

    """

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# Lookup Tables
# ---------------------------------------------------------------------------
ACTIVITY_TYPE_MAP: Final[dict[str, str]] = {
    "playing": "Playing",
    "streaming": "Streaming",
    "listening": "Listening to",
    "watching": "Watching",
    "competing": "Competing in",
}

TIME_UNIT_MULTIPLIERS: Final[dict[str, int]] = {
    "s": 1,
    "sec": 1,
    "second": 1,
    "seconds": 1,
    "m": 60,
    "min": 60,
    "minute": 60,
    "minutes": 60,
    "h": 3600,
    "hr": 3600,
    "hour": 3600,
    "hours": 3600,
    "d": 86400,
    "day": 86400,
    "days": 86400,
    "w": 604800,
    "week": 604800,
    "weeks": 604800,
}


# ---------------------------------------------------------------------------
# Embed Defaults
# ---------------------------------------------------------------------------
EMBED_COLOR_INFO: Final[int] = 0x3498DB      # Blue
EMBED_COLOR_SUCCESS: Final[int] = 0x2ECC71   # Green
EMBED_COLOR_WARNING: Final[int] = 0xF1C40F   # Yellow
EMBED_COLOR_ERROR: Final[int] = 0xE74C3C     # Red
EMBED_COLOR_NEUTRAL: Final[int] = 0x95A5A6    # Gray

MAX_EMBED_TITLE_LENGTH: Final[int] = 256
MAX_EMBED_DESCRIPTION_LENGTH: Final[int] = 4096
MAX_EMBED_FIELD_NAME_LENGTH: Final[int] = 256
MAX_EMBED_FIELD_VALUE_LENGTH: Final[int] = 1024
MAX_EMBED_FIELDS: Final[int] = 25


# ---------------------------------------------------------------------------
# Localization Defaults
# ---------------------------------------------------------------------------
DEFAULT_LOCALE: Final[str] = "en-US"
SUPPORTED_LOCALES: Final[tuple[str, ...]] = (
    "en-US",
    "en-GB",
    "es-ES",
    "fr-FR",
    "de-DE",
    "ja-JP",
    "ko-KR",
    "zh-CN",
    "zh-TW",
    "ru-RU",
    "pt-BR",
    "it-IT",
    "nl-NL",
    "pl-PL",
    "tr-TR",
)

