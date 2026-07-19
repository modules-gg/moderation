"""Configuration management for the moderation module.

This module provides a centralized, type-safe configuration system that
loads, validates, and exposes application settings. It serves as the
single source of truth for all runtime configuration.

Example:
    Access configuration values from anywhere in the codebase::

        from moderation.config import get_config

        cfg = get_config()
        token = cfg.bot.token
        prefix = cfg.bot.prefix

"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Self

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_PATH: Path = Path("config.json")
ENV_PREFIX: str = "MODERATION_"


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------
class ConfigValidationError(Exception):
    """Raised when a configuration value fails validation."""

    pass


class ConfigNotLoadedError(Exception):
    """Raised when configuration is accessed before being loaded."""

    pass


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class BotConfig:
    """Discord bot-specific configuration.

    Attributes:
        token: The Discord bot authentication token.
        prefix: The command prefix for prefix-based commands.
        owner_ids: List of Discord user IDs with owner-level privileges.
        description: The bot's description shown in help and profile.
        activity: Optional activity configuration for the bot's presence.
        intents: Discord gateway intents configuration.

    """

    token: str
    prefix: str = "!"
    owner_ids: list[int] = field(default_factory=list)
    description: str = "modules.gg Moderation Bot"
    activity: dict[str, str] = field(default_factory=dict)
    intents: dict[str, bool] = field(default_factory=dict)


@dataclass(frozen=True)
class LoggingConfig:
    """Logging subsystem configuration.

    Attributes:
        level: The minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        format: The log message format string.
        date_format: The date format string for log timestamps.
        file: File logging configuration.
        console: Console logging configuration.

    """

    level: str = "INFO"
    format: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"
    file: dict[str, Any] = field(default_factory=dict)
    console: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class ExtensionsConfig:
    """Extension (cog) loading configuration.

    Attributes:
        auto_load: Whether to fail startup if an extension fails to load.
        paths: List of dotted module paths to load as extensions.

    """

    auto_load: bool = True
    paths: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class DatabaseConfig:
    """Database connection configuration.

    Attributes:
        type: The database type (e.g., sqlite, postgresql, mysql).
        connection_string: The database connection URI.

    """

    type: str = "sqlite"
    connection_string: str = "sqlite:///data/moderation.db"


@dataclass(frozen=True)
class AppConfig:
    """Top-level application configuration container.

    This class aggregates all configuration sections into a single,
    immutable data structure.

    Attributes:
        bot: Discord bot configuration.
        logging: Logging subsystem configuration.
        extensions: Extension loading configuration.
        database: Database connection configuration.
        raw: The raw dictionary for accessing non-standard keys.

    """

    bot: BotConfig
    logging: LoggingConfig = field(default_factory=lambda: LoggingConfig())
    extensions: ExtensionsConfig = field(default_factory=lambda: ExtensionsConfig())
    database: DatabaseConfig = field(default_factory=lambda: DatabaseConfig())
    raw: dict[str, Any] = field(default_factory=dict, repr=False)


# ---------------------------------------------------------------------------
# Configuration Loader
# ---------------------------------------------------------------------------
class ConfigManager:
    """Manages the lifecycle of the application configuration.

    This class handles loading configuration from JSON files, environment
    variable overrides, and validation. It is designed as a singleton-like
    manager that caches the configuration after first load.

    Attributes:
        _instance: The singleton instance of ConfigManager.
        _config: The cached AppConfig instance.

    """

    _instance: ConfigManager | None = None
    _config: AppConfig | None = None

    def __new__(cls) -> Self:
        """Ensure only one ConfigManager instance exists."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def load(self, path: Path | str | None = None) -> AppConfig:
        """Load and validate configuration from a JSON file.

        Args:
            path: Path to the configuration file. Defaults to ``config.json``
                in the working directory.

        Returns:
            The validated :class:`AppConfig` instance.

        Raises:
            ConfigValidationError: If the configuration file is missing,
                malformed, or contains invalid values.

        """
        config_path = Path(path or DEFAULT_CONFIG_PATH)

        if not config_path.exists():
            raise ConfigValidationError(
                f"Configuration file not found: {config_path.resolve()}. "
                f"Copy 'config.example.json' to '{config_path.name}' and fill in your values."
            )

        try:
            with config_path.open(encoding="utf-8") as file:
                raw_data: dict[str, Any] = json.load(file)
        except json.JSONDecodeError as exc:
            raise ConfigValidationError(
                f"Invalid JSON in configuration file '{config_path}': {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigValidationError(
                f"Unable to read configuration file '{config_path}': {exc}"
            ) from exc

        # Remove comment keys
        raw_data.pop("_comment", None)

        # Apply environment variable overrides
        raw_data = self._apply_env_overrides(raw_data)

        # Build typed configuration
        app_config = self._build_config(raw_data)
        self._config = app_config

        return app_config

    def get(self) -> AppConfig:
        """Retrieve the currently loaded configuration.

        Returns:
            The cached :class:`AppConfig` instance.

        Raises:
            ConfigNotLoadedError: If :meth:`load` has not been called.

        """
        if self._config is None:
            raise ConfigNotLoadedError(
                "Configuration has not been loaded. Call load() first."
            )
        return self._config

    def reload(self, path: Path | str | None = None) -> AppConfig:
        """Reload configuration from disk.

        This is useful for hot-reloading configuration without restarting
        the bot. Note that some values (e.g., intents) may require a restart
        to take effect.

        Args:
            path: Path to the configuration file. Defaults to the path
                used in the previous :meth:`load` call, or ``config.json``.

        Returns:
            The newly loaded :class:`AppConfig` instance.

        """
        self._config = None
        return self.load(path)

    @staticmethod
    def _apply_env_overrides(data: dict[str, Any]) -> dict[str, Any]:
        """Override configuration values with environment variables.

        Environment variables are expected in the format::
        
            MODERATION_SECTION_KEY=value
        
        For example, ``MODERATION_BOT_TOKEN=abc123`` overrides ``bot.token``.

        Args:
            data: The raw configuration dictionary.

        Returns:
            The dictionary with environment overrides applied.

        """
        for key, value in os.environ.items():
            if not key.startswith(ENV_PREFIX):
                continue

            # Format: MODERATION_SECTION_SUBKEY=value
            parts = key[len(ENV_PREFIX) :].lower().split("_", 1)
            if len(parts) != 2:
                continue

            section, subkey = parts
            if section not in data:
                continue

            section_data = data[section]
            if isinstance(section_data, dict) and subkey in section_data:
                # Attempt type coercion based on existing value
                existing = section_data[subkey]
                if isinstance(existing, bool):
                    section_data[subkey] = value.lower() in ("true", "1", "yes", "on")
                elif isinstance(existing, int):
                    try:
                        section_data[subkey] = int(value)
                    except ValueError:
                        section_data[subkey] = value
                elif isinstance(existing, list):
                    section_data[subkey] = [item.strip() for item in value.split(",")]
                else:
                    section_data[subkey] = value

        return data

    @staticmethod
    def _build_config(raw: dict[str, Any]) -> AppConfig:
        """Construct a typed AppConfig from raw dictionary data.

        Args:
            raw: The raw configuration dictionary.

        Returns:
            A fully populated :class:`AppConfig` instance.

        Raises:
            ConfigValidationError: If required sections or values are missing.

        """
        if "bot" not in raw:
            raise ConfigValidationError("Missing required configuration section: 'bot'")

        bot_raw = raw.get("bot", {})
        if "token" not in bot_raw or not bot_raw["token"]:
            raise ConfigValidationError(
                "Missing required configuration value: 'bot.token'. "
                "Please set your Discord bot token."
            )

        # Convert owner_ids to integers
        owner_ids_raw = bot_raw.get("owner_ids", [])
        owner_ids = [int(uid) for uid in owner_ids_raw if isinstance(uid, (int, str))]

        bot_config = BotConfig(
            token=str(bot_raw.get("token", "")),
            prefix=str(bot_raw.get("prefix", "!")),
            owner_ids=owner_ids,
            description=str(bot_raw.get("description", "modules.gg Moderation Bot")),
            activity=dict(bot_raw.get("activity", {})),
            intents=dict(bot_raw.get("intents", {})),
        )

        logging_raw = raw.get("logging", {})
        logging_config = LoggingConfig(
            level=str(logging_raw.get("level", "INFO")).upper(),
            format=str(logging_raw.get("format", "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")),
            date_format=str(logging_raw.get("date_format", "%Y-%m-%d %H:%M:%S")),
            file=dict(logging_raw.get("file", {})),
            console=dict(logging_raw.get("console", {})),
        )

        extensions_raw = raw.get("extensions", {})
        extensions_config = ExtensionsConfig(
            auto_load=bool(extensions_raw.get("auto_load", True)),
            paths=list(extensions_raw.get("paths", [])),
        )

        database_raw = raw.get("database", {})
        database_config = DatabaseConfig(
            type=str(database_raw.get("type", "sqlite")),
            connection_string=str(database_raw.get("connection_string", "sqlite:///data/moderation.db")),
        )

        return AppConfig(
            bot=bot_config,
            logging=logging_config,
            extensions=extensions_config,
            database=database_config,
            raw=raw,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def load_config(path: Path | str | None = None) -> AppConfig:
    """Load configuration from a file.

    This is a convenience function that delegates to :class:`ConfigManager`.

    Args:
        path: Path to the configuration file.

    Returns:
        The loaded :class:`AppConfig` instance.

    """
    return ConfigManager().load(path)


def get_config() -> AppConfig:
    """Get the currently loaded configuration.

    Returns:
        The cached :class:`AppConfig` instance.

    Raises:
        ConfigNotLoadedError: If configuration has not been loaded.

    """
    return ConfigManager().get()


def reload_config(path: Path | str | None = None) -> AppConfig:
    """Reload configuration from disk.

    Args:
        path: Path to the configuration file.

    Returns:
        The newly loaded :class:`AppConfig` instance.

    """
    return ConfigManager().reload(path)
           
