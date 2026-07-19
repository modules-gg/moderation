"""Permission and hierarchy check exceptions.

These exceptions are raised when a moderation action is blocked due to
insufficient permissions, role hierarchy violations, or other access
control failures.

"""

from __future__ import annotations

from moderation.exceptions.base import ModerationError


class InsufficientPermissionsError(ModerationError):
    """Raised when a user lacks the required permissions for an action.

    This is the primary exception for permission-related failures in
    moderation commands.

    Attributes:
        required_permission: The permission that was missing.
        user_id: The Discord ID of the user who lacked permission.

    """

    def __init__(
        self,
        message: str,
        *,
        required_permission: str | None = None,
        user_id: int | None = None,
        code: str = "PERM_INSUFFICIENT",
    ) -> None:
        """Initialize with optional permission and user context."""
        super().__init__(message, code=code)
        self.required_permission: str | None = required_permission
        self.user_id: int | None = user_id


class HierarchyViolationError(ModerationError):
    """Raised when a user attempts to moderate someone with equal or higher role hierarchy.

    Discord's role hierarchy prevents users from taking action against others
    who have equal or higher top roles. This exception enforces that rule.

    Attributes:
        target_id: The Discord ID of the user who could not be actioned.
        target_top_role: The name of the target's highest role.

    """

    def __init__(
        self,
        message: str,
        *,
        target_id: int | None = None,
        target_top_role: str | None = None,
        code: str = "HIERARCHY_VIOLATION",
    ) -> None:
        """Initialize with optional target context."""
        super().__init__(message, code=code)
        self.target_id: int | None = target_id
        self.target_top_role: str | None = target_top_role


class BotHierarchyError(ModerationError):
    """Raised when the bot's role is too low to perform an action.

    The bot must have a higher top role than the target user to perform
    most moderation actions. This exception is raised when that condition
    is not met.

    Attributes:
        bot_top_role: The name of the bot's highest role.
        target_top_role: The name of the target's highest role.

    """

    def __init__(
        self,
        message: str,
        *,
        bot_top_role: str | None = None,
        target_top_role: str | None = None,
        code: str = "BOT_HIERARCHY_LOW",
    ) -> None:
        """Initialize with optional role context."""
        super().__init__(message, code=code)
        self.bot_top_role: str | None = bot_top_role
        self.target_top_role: str | None = target_top_role


class SelfModerationError(ModerationError):
    """Raised when a user attempts to moderate themselves.

    Most moderation actions (kick, ban, timeout, etc.) cannot be applied
    to the invoking user for safety and logical reasons.

    Attributes:
        action: The moderation action that was attempted.

    """

    def __init__(
        self,
        message: str = "You cannot perform this action on yourself.",
        *,
        action: str | None = None,
        code: str = "SELF_MODERATION",
    ) -> None:
        """Initialize with optional action context."""
        super().__init__(message, code=code)
        self.action: str | None = action


class OwnerImmuneError(ModerationError):
    """Raised when an action is attempted against a bot owner or server owner.

    Owners are immune to most moderation actions to prevent accidental
    lockouts or abuse.

    Attributes:
        target_id: The Discord ID of the immune user.
        reason: The reason for immunity (bot_owner or guild_owner).

    """

    def __init__(
        self,
        message: str,
        *,
        target_id: int | None = None,
        reason: str | None = None,
        code: str = "OWNER_IMMUNE",
    ) -> None:
        """Initialize with optional target and reason context."""
        super().__init__(message, code=code)
        self.target_id: int | None = target_id
        self.reason: str | None = reason
      
