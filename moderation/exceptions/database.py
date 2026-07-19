"""Database operation exceptions.

These exceptions are raised when database interactions fail, including
connection issues, query errors, constraint violations, and migration
failures.

"""

from __future__ import annotations

from moderation.exceptions.base import ModerationError


class RecordNotFoundError(ModerationError):
    """Raised when a database query returns no matching records.

    This is distinct from :class:`ActionNotFoundError` and
    :class:`CaseNotFoundError` in that it represents a low-level
    database failure rather than a business logic lookup failure.

    Attributes:
        table: The database table that was queried.
        query_params: The parameters used in the query.

    """

    def __init__(
        self,
        message: str,
        *,
        table: str | None = None,
        query_params: dict[str, object] | None = None,
        code: str = "DB_RECORD_NOT_FOUND",
    ) -> None:
        """Initialize with optional table and query context."""
        super().__init__(message, code=code)
        self.table: str | None = table
        self.query_params: dict[str, object] | None = query_params


class DuplicateRecordError(ModerationError):
    """Raised when an insert or update would violate a unique constraint.

    This typically occurs when attempting to create a record that
    already exists, such as a duplicate case number or user entry.

    Attributes:
        table: The database table where the conflict occurred.
        field: The field or column that caused the duplicate.

    """

    def __init__(
        self,
        message: str,
        *,
        table: str | None = None,
        field: str | None = None,
        code: str = "DB_DUPLICATE",
    ) -> None:
        """Initialize with optional table and field context."""
        super().__init__(message, code=code)
        self.table: str | None = table
        self.field: str | None = field


class ConnectionPoolExhaustedError(ModerationError):
    """Raised when all database connections are in use.

    This indicates the application is under heavy load or connections
    are not being released properly. Consider increasing the pool size
    or investigating connection leaks.

    Attributes:
        max_connections: The configured maximum pool size.

    """

    def __init__(
        self,
        message: str = "Database connection pool exhausted.",
        *,
        max_connections: int | None = None,
        code: str = "DB_POOL_EXHAUSTED",
    ) -> None:
        """Initialize with optional pool size context."""
        super().__init__(message, code=code)
        self.max_connections: int | None = max_connections


class MigrationError(ModerationError):
    """Raised when a database migration fails to apply or rollback.

    Migration failures can leave the database in an inconsistent state.
    This exception includes the migration name to aid in recovery.

    Attributes:
        migration_name: The name of the migration that failed.
        is_upgrade: Whether the failure occurred during upgrade or downgrade.

    """

    def __init__(
        self,
        message: str,
        *,
        migration_name: str | None = None,
        is_upgrade: bool = True,
        code: str = "DB_MIGRATION_FAILED",
    ) -> None:
        """Initialize with optional migration context."""
        super().__init__(message, code=code)
        self.migration_name: str | None = migration_name
        self.is_upgrade: bool = is_upgrade
      
