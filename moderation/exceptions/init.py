"""Custom exceptions for the moderation module.

This package defines all domain-specific exceptions used throughout the
project. Centralizing exceptions improves error handling consistency
and makes it easier for callers to catch specific failure modes.

Example:
    Catch a specific moderation error::

        from moderation.exceptions import ModerationError, InsufficientPermissionsError

        try:
            await moderator.kick(user, reason="Spam")
        except InsufficientPermissionsError as exc:
            await ctx.send(str(exc))

"""

from __future__ import annotations

from moderation.exceptions.base import (
    ModerationError,
    ConfigurationError,
    DatabaseError,
    ValidationError,
)
from moderation.exceptions.checks import (
    InsufficientPermissionsError,
    HierarchyViolationError,
    BotHierarchyError,
    SelfModerationError,
    OwnerImmuneError,
)
from moderation.exceptions.commands import (
    CommandError,
    InvalidDurationError,
    InvalidUserError,
    InvalidChannelError,
    InvalidRoleError,
    ActionFailedError,
    ActionNotFoundError,
    CaseNotFoundError,
)
from moderation.exceptions.database import (
    RecordNotFoundError,
    DuplicateRecordError,
    ConnectionPoolExhaustedError,
    MigrationError,
)

__all__ = [
    # Base
    "ModerationError",
    "ConfigurationError",
    "DatabaseError",
    "ValidationError",
    # Checks
    "InsufficientPermissionsError",
    "HierarchyViolationError",
    "BotHierarchyError",
    "SelfModerationError",
    "OwnerImmuneError",
    # Commands
    "CommandError",
    "InvalidDurationError",
    "InvalidUserError",
    "InvalidChannelError",
    "InvalidRoleError",
    "ActionFailedError",
    "ActionNotFoundError",
    "CaseNotFoundError",
    # Database
    "RecordNotFoundError",
    "DuplicateRecordError",
    "ConnectionPoolExhaustedError",
    "MigrationError",
]
