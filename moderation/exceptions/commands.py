"""Command execution and input validation exceptions.

These exceptions are raised during command parsing, argument validation,
or when a moderation action fails to execute successfully.

"""

from __future__ import annotations

from moderation.exceptions.base import ModerationError


class CommandError(ModerationError):
    """Raised when a command fails to execute for a general reason.

    This is the base exception for all command-related errors. More
    specific exceptions should be used where possible.

    """

    def __init__(self, message: str, *, code: str = "COMMAND_ERROR") -> None:
        """Initialize with a default error code."""
        super().__init__(message, code=code)


class InvalidDurationError(ModerationError):
    """Raised when a duration string cannot be parsed or is out of bounds.

    Duration strings are expected in formats like ``1h30m``, ``2d``,
    or ``1w``. This exception is raised when the input does not match
    any supported format or exceeds Discord's limits.

    Attributes:
        input_value: The raw string that failed parsing.
        max_allowed: The maximum duration allowed, in seconds.

    """

    def __init__(
        self,
        message: str,
        *,
        input_value: str | None = None,
        max_allowed: int | None = None,
        code: str = "DURATION_INVALID",
    ) -> None:
        """Initialize with optional duration context."""
        super().__init__(message, code=code)
        self.input_value: str | None = input_value
        self.max_allowed: int | None = max_allowed


class InvalidUserError(ModerationError):
    """Raised when a user mention, ID, or username cannot be resolved.

    This covers cases where the target user is not found in the guild,
    has left, or the provided identifier is malformed.

    Attributes:
        input_value: The raw string that failed resolution.

    """

    def __init__(
        self,
        message: str,
        *,
        input_value: str | None = None,
        code: str = "USER_INVALID",
    ) -> None:
        """Initialize with optional input context."""
        super().__init__(message, code=code)
        self.input_value: str | None = input_value


class InvalidChannelError(ModerationError):
    """Raised when a channel mention, ID, or name cannot be resolved.

    Attributes:
        input_value: The raw string that failed resolution.

    """

    def __init__(
        self,
        message: str,
        *,
        input_value: str | None = None,
        code: str = "CHANNEL_INVALID",
    ) -> None:
        """Initialize with optional input context."""
        super().__init__(message, code=code)
        self.input_value: str | None = input_value


class InvalidRoleError(ModerationError):
    """Raised when a role mention, ID, or name cannot be resolved.

    Attributes:
        input_value: The raw string that failed resolution.

    """

    def __init__(
        self,
        message: str,
        *,
        input_value: str | None = None,
        code: str = "ROLE_INVALID",
    ) -> None:
        """Initialize with optional input context."""
        super().__init__(message, code=code)
        self.input_value: str | None = input_value


class ActionFailedError(ModerationError):
    """Raised when a moderation action fails to complete after validation.

    This covers Discord API failures, network errors, or unexpected
    conditions that prevent an otherwise valid action from succeeding.

    Attributes:
        action: The moderation action that failed (e.g., kick, ban).
        target_id: The Discord ID of the target user.

    """

    def __init__(
        self,
        message: str,
        *,
        action: str | None = None,
        target_id: int | None = None,
        code: str = "ACTION_FAILED",
    ) -> None:
        """Initialize with optional action context."""
        super().__init__(message, code=code)
        self.action: str | None = action
        self.target_id: int | None = target_id


class ActionNotFoundError(ModerationError):
    """Raised when a requested moderation action does not exist.

    This is primarily used in the case system when looking up
    historical actions by ID.

    Attributes:
        action_id: The identifier that was not found.

    """

    def __init__(
        self,
        message: str,
        *,
        action_id: int | None = None,
        code: str = "ACTION_NOT_FOUND",
    ) -> None:
        """Initialize with optional action ID context."""
        super().__init__(message, code=code)
        self.action_id: int | None = action_id


class CaseNotFoundError(ModerationError):
    """Raised when a moderation case cannot be found by its case number.

    Attributes:
        case_id: The case number that was not found.

    """

    def __init__(
        self,
        message: str,
        *,
        case_id: int | None = None,
        code: str = "CASE_NOT_FOUND",
    ) -> None:
        """Initialize with optional case ID context."""
        super().__init__(message, code=code)
        self.case_id: int | None = case_id
      
