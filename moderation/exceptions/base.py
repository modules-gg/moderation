"""Base exception classes for the moderation module.

All custom exceptions in this project inherit from :class:`ModerationError`,
allowing callers to catch any domain-specific error with a single except block.

"""

from __future__ import annotations


class ModerationError(Exception):
    """Base exception for all moderation module errors.

    This is the root of the exception hierarchy. Catching this class
    will catch any custom exception raised by the moderation module.

    Attributes:
        message: A human-readable description of the error.
        code: An optional machine-readable error code for programmatic handling.

    """

    def __init__(self, message: str, *, code: str | None = None) -> None:
        """Initialize the exception with a message and optional code.

        Args:
            message: The error description.
            code: An optional error identifier for client-side handling.

        """
        super().__init__(message)
        self.message: str = message
        self.code: str | None = code

    def __str__(self) -> str:
        """Return the error message."""
        return self.message

    def __repr__(self) -> str:
        """Return a developer-friendly representation."""
        if self.code:
            return f"{self.__class__.__name__}(code={self.code!r}, message={self.message!r})"
        return f"{self.__class__.__name__}({self.message!r})"


class ConfigurationError(ModerationError):
    """Raised when the application configuration is invalid or missing.

    This includes missing config files, invalid JSON, missing required keys,
    or values that fail validation.

    """

    def __init__(self, message: str, *, code: str = "CONFIG_INVALID") -> None:
        """Initialize with a default error code."""
        super().__init__(message, code=code)


class DatabaseError(ModerationError):
    """Raised when a database operation fails.

    This covers connection failures, query errors, constraint violations,
    and other database-related problems.

    """

    def __init__(self, message: str, *, code: str = "DB_ERROR") -> None:
        """Initialize with a default error code."""
        super().__init__(message, code=code)


class ValidationError(ModerationError):
    """Raised when user input or data fails validation.

    This is a general-purpose validation exception used when more specific
    exceptions (e.g., :class:`InvalidDurationError`) are not appropriate.

    """

    def __init__(self, message: str, *, code: str = "VALIDATION_FAILED") -> None:
        """Initialize with a default error code."""
        super().__init__(message, code=code)
  
