"""Database connection management for the moderation module.

This module provides a centralized database connection pool and
session management. It supports SQLite for development and can be
extended for PostgreSQL or MySQL in production.

Version 1.1 will implement full ORM models and the case system.
For now, connection lifecycle and basic query execution are provided.

"""

from __future__ import annotations

import asyncio
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, AsyncGenerator

from moderation.config import get_config
from moderation.constants import DB_TIMEOUT, DEFAULT_DB_PATH, MAX_DB_CONNECTIONS
from moderation.exceptions.database import ConnectionPoolExhaustedError, DatabaseError
from moderation.logger import get_logger

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Connection Pool
# ---------------------------------------------------------------------------
class ConnectionPool:
    """Async-aware database connection pool.

    Manages a pool of SQLite connections with async-compatible access.
    For production deployments, this should be replaced with an async
    driver like ``aiosqlite`` or ``asyncpg``.

    Attributes:
        _database_path: Path to the SQLite database file.
        _max_connections: Maximum number of concurrent connections.
        _semaphore: Async semaphore for connection limiting.
        _initialized: Whether the pool has been set up.

    """

    def __init__(
        self,
        database_path: str | Path | None = None,
        max_connections: int = MAX_DB_CONNECTIONS,
    ) -> None:
        """Initialize the connection pool.

        Args:
            database_path: Path to the SQLite database. Defaults to config value.
            max_connections: Maximum concurrent connections.

        """
        self._database_path: Path = Path(database_path or DEFAULT_DB_PATH)
        self._max_connections: int = max_connections
        self._semaphore: asyncio.Semaphore = asyncio.Semaphore(max_connections)
        self._initialized: bool = False

    async def initialize(self) -> None:
        """Create the database directory and initialize the pool.

        Raises:
            DatabaseError: If the database directory cannot be created.

        """
        if self._initialized:
            return

        try:
            self._database_path.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise DatabaseError(
                f"Failed to create database directory '{self._database_path.parent}': {exc}"
            ) from exc

        # Test connection
        try:
            conn = sqlite3.connect(str(self._database_path), timeout=DB_TIMEOUT)
            conn.execute("SELECT 1")
            conn.close()
        except sqlite3.Error as exc:
            raise DatabaseError(
                f"Failed to connect to database '{self._database_path}': {exc}"
            ) from exc

        self._initialized = True
        logger.info(
            "Database pool initialized: %s (max connections: %d)",
            self._database_path,
            self._max_connections,
        )

    async def close(self) -> None:
        """Close the connection pool and release resources.

        SQLite connections are created per-acquisition, so this mainly
        resets the initialization state.

        """
        self._initialized = False
        logger.info("Database pool closed.")

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[sqlite3.Connection, None]:
        """Acquire a database connection from the pool.

        Yields:
            An active :class:`sqlite3.Connection` instance.

        Raises:
            ConnectionPoolExhaustedError: If all connections are in use.
            DatabaseError: If connection acquisition fails.

        Example:
            async with pool.acquire() as conn:
                cursor = conn.execute("SELECT * FROM cases")
                rows = cursor.fetchall()

        """
        if not self._initialized:
            await self.initialize()

        acquired = await asyncio.wait_for(
            self._semaphore.acquire(),
            timeout=DB_TIMEOUT,
        )

        if not acquired:
            raise ConnectionPoolExhaustedError(
                f"All {self._max_connections} database connections are in use.",
                max_connections=self._max_connections,
            )

        conn: sqlite3.Connection | None = None
        try:
            conn = sqlite3.connect(
                str(self._database_path),
                timeout=DB_TIMEOUT,
                detect_types=sqlite3.PARSE_DECLTYPES,
            )
            conn.row_factory = sqlite3.Row
            yield conn
        except sqlite3.Error as exc:
            raise DatabaseError(f"Database operation failed: {exc}") from exc
        finally:
            if conn is not None:
                conn.close()
            self._semaphore.release()

    async def execute(
        self,
        sql: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> sqlite3.Cursor:
        """Execute a SQL statement and return the cursor.

        Args:
            sql: The SQL statement to execute.
            parameters: Optional parameters for parameterized queries.

        Returns:
            The :class:`sqlite3.Cursor` after execution.

        Raises:
            DatabaseError: If execution fails.

        """
        async with self.acquire() as conn:
            try:
                if parameters:
                    return conn.execute(sql, parameters)
                return conn.execute(sql)
            except sqlite3.Error as exc:
                raise DatabaseError(f"Query failed: {exc}\nSQL: {sql}") from exc

    async def executescript(self, sql: str) -> sqlite3.Cursor:
        """Execute a SQL script (multiple statements).

        Args:
            sql: The SQL script to execute.

        Returns:
            The :class:`sqlite3.Cursor` after execution.

        Raises:
            DatabaseError: If execution fails.

        """
        async with self.acquire() as conn:
            try:
                return conn.executescript(sql)
            except sqlite3.Error as exc:
                raise DatabaseError(f"Script failed: {exc}") from exc

    async def fetchone(
        self,
        sql: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> sqlite3.Row | None:
        """Execute a query and return the first row.

        Args:
            sql: The SQL query.
            parameters: Optional query parameters.

        Returns:
            The first row, or None if no results.

        """
        async with self.acquire() as conn:
            cursor = conn.execute(sql, parameters or ())
            return cursor.fetchone()

    async def fetchall(
        self,
        sql: str,
        parameters: tuple[Any, ...] | None = None,
    ) -> list[sqlite3.Row]:
        """Execute a query and return all rows.

        Args:
            sql: The SQL query.
            parameters: Optional query parameters.

        Returns:
            A list of result rows.

        """
        async with self.acquire() as conn:
            cursor = conn.execute(sql, parameters or ())
            return cursor.fetchall()


# ---------------------------------------------------------------------------
# Singleton Instance
# ---------------------------------------------------------------------------
_pool: ConnectionPool | None = None


def get_pool() -> ConnectionPool:
    """Get the global connection pool instance.

    Returns:
        The :class:`ConnectionPool` singleton.

    """
    global _pool
    if _pool is None:
        try:
            config = get_config()
            db_config = config.database
            _pool = ConnectionPool(
                database_path=db_config.connection_string.replace("sqlite:///", ""),
                max_connections=MAX_DB_CONNECTIONS,
            )
        except Exception:
            _pool = ConnectionPool()
    return _pool


async def initialize_database() -> None:
    """Initialize the global database pool.

    This should be called during bot startup before any database
    operations are performed.

    """
    pool = get_pool()
    await pool.initialize()


async def close_database() -> None:
    """Close the global database pool.

    This should be called during bot shutdown to ensure all
    connections are properly released.

    """
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None
