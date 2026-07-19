"""Logging subsystem for the moderation module.

This module provides a centralized logging factory that configures
handlers, formatters, and log levels based on the application configuration.
It ensures consistent logging across all components of the bot.

Example:
    Get a logger for your module::

        from moderation.logger import get_logger

        logger = get_logger(__name__)
        logger.info("Something happened")
        logger.debug("Diagnostic data: %s", data)

"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

from moderation.config import AppConfig, ConfigNotLoadedError, get_config

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"
DEFAULT_LOG_LEVEL: str = "INFO"
DEFAULT_MAX_BYTES: int = 10_485_760  # 10 MiB
DEFAULT_BACKUP_COUNT: int = 5


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------
class LoggingSetupError(Exception):
    """Raised when the logging subsystem fails to initialize."""

    pass


# ---------------------------------------------------------------------------
# Logger Factory
# ---------------------------------------------------------------------------
class LoggerFactory:
    """Factory for creating and configuring loggers.

    This class manages the lifecycle of the logging subsystem, including
    handler setup, formatter configuration, and level management. It is
    designed to be initialized once during bot startup.

    Attributes:
        _initialized: Whether the factory has been configured.
        _root_logger: The root logger for the moderation package.

    """

    _instance: LoggerFactory | None = None
    _initialized: bool = False
    _root_logger: logging.Logger | None = None

    def __new__(cls) -> LoggerFactory:
        """Ensure only one LoggerFactory instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: AppConfig | None = None) -> logging.Logger:
        """Initialize the logging subsystem.

        Configures the root logger with console and optional file handlers
        based on the provided or loaded configuration.

        Args:
            config: An optional :class:`AppConfig` instance. If not provided,
                the configuration will be loaded automatically.

        Returns:
            The configured root :class:`logging.Logger`.

        Raises:
            LoggingSetupError: If the logging subsystem cannot be initialized.
            ConfigNotLoadedError: If no configuration is available.

        """
        if self._initialized and self._root_logger is not None:
            return self._root_logger

        if config is None:
            try:
                config = get_config()
            except ConfigNotLoadedError as exc:
                raise LoggingSetupError(
                    "Cannot initialize logging without configuration. "
                    "Call load_config() first or pass a config object."
                ) from exc

        log_cfg = config.logging

        # Determine log level
        level_name: str = log_cfg.level.upper()
        try:
            level: int = getattr(logging, level_name)
        except AttributeError:
            level = logging.INFO

        # Create root logger
        root_logger = logging.getLogger("moderation")
        root_logger.setLevel(level)

        # Clear existing handlers to prevent duplicates
        if root_logger.handlers:
            root_logger.handlers.clear()

        # Create formatter
        fmt: str = log_cfg.format or DEFAULT_LOG_FORMAT
        date_fmt: str = log_cfg.date_format or DEFAULT_DATE_FORMAT
        formatter = logging.Formatter(fmt, datefmt=date_fmt)

        # Console handler
        console_cfg: dict[str, Any] = log_cfg.console
        if console_cfg.get("enabled", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            console_handler.setLevel(level)
            root_logger.addHandler(console_handler)

        # File handler with rotation
        file_cfg: dict[str, Any] = log_cfg.file
        if file_cfg.get("enabled", False):
            log_path = Path(file_cfg.get("path", "logs/moderation.log"))
            try:
                log_path.parent.mkdir(parents=True, exist_ok=True)
            except OSError as exc:
                raise LoggingSetupError(
                    f"Failed to create log directory '{log_path.parent}': {exc}"
                ) from exc

            max_bytes: int = file_cfg.get("max_bytes", DEFAULT_MAX_BYTES)
            backup_count: int = file_cfg.get("backup_count", DEFAULT_BACKUP_COUNT)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            file_handler.setLevel(level)
            root_logger.addHandler(file_handler)

        # Reduce noise from discord.py
        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.WARNING)

        # Reduce noise from aiohttp
        aiohttp_logger = logging.getLogger("aiohttp")
        aiohttp_logger.setLevel(logging.WARNING)

        self._root_logger = root_logger
        self._initialized = True

        root_logger.debug("Logging subsystem initialized at level '%s'.", level_name)
        return root_logger

    def shutdown(self) -> None:
        """Gracefully shut down the logging subsystem.

        Flushes and closes all handlers to ensure no log messages are lost.

        """
        if self._root_logger is None:
            return

        for handler in self._root_logger.handlers:
            handler.flush()
            handler.close()

        self._root_logger.handlers.clear()
        self._initialized = False
        self._root_logger = None


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    This function returns a child logger of the moderation root logger.
    All loggers share the same handlers and configuration.

    Args:
        name: The logger name, typically ``__name__`` of the calling module.

    Returns:
        A configured :class:`logging.Logger` instance.

    Example::
    
        logger = get_logger(__name__)
        logger.info("Module initialized")

    """
    return logging.getLogger(f"moderation.{name}")


def initialize_logging(config: AppConfig | None = None) -> logging.Logger:
    """Initialize the logging subsystem.

    This is a convenience function that delegates to :class:`LoggerFactory`.

    Args:
        config: An optional :class:`AppConfig` instance.

    Returns:
        The configured root :class:`logging.Logger`.

    """
    return LoggerFactory().initialize(config)


def shutdown_logging() -> None:
    """Shut down the logging subsystem.

    This is a convenience function that delegates to :class:`LoggerFactory`.

    """
    LoggerFactory().shutdown()

