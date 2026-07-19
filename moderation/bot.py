"""Core bot client and lifecycle management for the moderation module.

This module defines the :class:`ModerationBot` class, which extends
:class:`discord.ext.commands.Bot` to provide:

- Startup sequence with configuration loading
- Structured logging initialization
- Dynamic extension (cog) loading
- Ready event handling
- Graceful shutdown with cleanup

Example:
    Basic usage::

        import asyncio
        from moderation.bot import ModerationBot

        async def main() -> None:
            bot = ModerationBot()
            await bot.start()

        if __name__ == "__main__":
            asyncio.run(main())

"""

from __future__ import annotations

import asyncio
import json
import logging
import logging.handlers
import os
import signal
import sys
from pathlib import Path
from typing import Any

import discord
from discord.ext import commands

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
DEFAULT_CONFIG_PATH: Path = Path("config.json")
DEFAULT_LOG_FORMAT: str = "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
DEFAULT_DATE_FORMAT: str = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Custom Exceptions
# ---------------------------------------------------------------------------
class ConfigurationError(Exception):
    """Raised when the bot configuration is invalid or missing."""

    pass


class ExtensionLoadError(Exception):
    """Raised when an extension fails to load during startup."""

    pass


# ---------------------------------------------------------------------------
# ModerationBot
# ---------------------------------------------------------------------------
class ModerationBot(commands.Bot):
    """The primary Discord bot client for the moderation module.

    This class manages the bot's lifecycle, including configuration loading,
    logging setup, extension management, and graceful shutdown. It is designed
    to be instantiated once and run via :meth:`start` or :meth:`run`.

    Attributes:
        config (dict[str, Any]): The loaded configuration dictionary.
        logger (logging.Logger): The root logger for the moderation module.
        _shutdown_event (asyncio.Event): Internal event used to coordinate
            graceful shutdown.

    """

    def __init__(self, config_path: Path | str | None = None) -> None:
        """Initialize the ModerationBot instance.

        Loads configuration from disk, initializes logging, and configures
        Discord intents based on the configuration file.

        Args:
            config_path: Path to the JSON configuration file. Defaults to
                ``config.json`` in the working directory.

        Raises:
            ConfigurationError: If the configuration file cannot be found or
                parsed, or if required keys are missing.

        """
        self.config: dict[str, Any] = self._load_config(config_path or DEFAULT_CONFIG_PATH)
        self.logger: logging.Logger = self._setup_logging()
        self._shutdown_event: asyncio.Event = asyncio.Event()

        # Extract bot-specific configuration
        bot_config: dict[str, Any] = self.config.get("bot", {})

        # Build Discord intents from configuration
        intents_config: dict[str, bool] = bot_config.get("intents", {})
        intents = discord.Intents.default()
        for intent_name, enabled in intents_config.items():
            if hasattr(intents, intent_name) and isinstance(enabled, bool):
                setattr(intents, intent_name, enabled)

        # Determine command prefix
        prefix: str = bot_config.get("prefix", "!")

        super().__init__(
            command_prefix=commands.when_mentioned_or(prefix),
            intents=intents,
            description=bot_config.get("description", "modules.gg Moderation Bot"),
            help_command=None,  # We will implement a custom help command later
        )

        self.logger.info("ModerationBot initialized successfully.")

    # -----------------------------------------------------------------------
    # Configuration Loading
    # -----------------------------------------------------------------------
    @staticmethod
    def _load_config(path: Path | str) -> dict[str, Any]:
        """Load and validate the bot configuration from a JSON file.

        Args:
            path: Filesystem path to the configuration file.

        Returns:
            A dictionary containing the parsed configuration.

        Raises:
            ConfigurationError: If the file does not exist, cannot be read,
                or contains invalid JSON.

        """
        config_path = Path(path)

        if not config_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {config_path.resolve()}. "
                f"Please copy 'config.example.json' to '{config_path.name}' "
                f"and fill in your bot token."
            )

        try:
            with config_path.open(encoding="utf-8") as file:
                config: dict[str, Any] = json.load(file)
        except json.JSONDecodeError as exc:
            raise ConfigurationError(
                f"Invalid JSON in configuration file '{config_path}': {exc}"
            ) from exc
        except OSError as exc:
            raise ConfigurationError(
                f"Unable to read configuration file '{config_path}': {exc}"
            ) from exc

        # Validate required top-level keys
        required_keys = {"bot"}
        missing_keys = required_keys - config.keys()
        if missing_keys:
            raise ConfigurationError(
                f"Missing required configuration section(s): {', '.join(sorted(missing_keys))}"
            )

        # Validate required bot keys
        bot_config = config.get("bot", {})
        if "token" not in bot_config or not bot_config["token"]:
            raise ConfigurationError(
                "Missing required configuration value: 'bot.token'. "
                "Please set your Discord bot token in the configuration file."
            )

        return config

    # -----------------------------------------------------------------------
    # Logging Setup
    # -----------------------------------------------------------------------
    def _setup_logging(self) -> logging.Logger:
        """Configure the logging subsystem for the moderation module.

        Sets up both console and optional file handlers based on the
        configuration file. Returns the root logger for the package.

        Returns:
            The configured :class:`logging.Logger` instance.

        """
        log_config: dict[str, Any] = self.config.get("logging", {})
        log_level: str = log_config.get("level", "INFO").upper()
        log_format: str = log_config.get("format", DEFAULT_LOG_FORMAT)
        date_format: str = log_config.get("date_format", DEFAULT_DATE_FORMAT)

        # Create the root logger
        logger = logging.getLogger("moderation")
        logger.setLevel(getattr(logging, log_level, logging.INFO))

        # Prevent duplicate handlers if re-initialized
        if logger.handlers:
            logger.handlers.clear()

        formatter = logging.Formatter(log_format, datefmt=date_format)

        # Console handler
        console_config: dict[str, Any] = log_config.get("console", {})
        if console_config.get("enabled", True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler with rotation
        file_config: dict[str, Any] = log_config.get("file", {})
        if file_config.get("enabled", False):
            log_path = Path(file_config.get("path", "logs/moderation.log"))
            log_path.parent.mkdir(parents=True, exist_ok=True)

            max_bytes: int = file_config.get("max_bytes", 10_485_760)  # 10 MiB
            backup_count: int = file_config.get("backup_count", 5)

            file_handler = logging.handlers.RotatingFileHandler(
                filename=log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        # Reduce noise from discord.py's own logger
        discord_logger = logging.getLogger("discord")
        discord_logger.setLevel(logging.WARNING)

        logger.info("Logging subsystem initialized at level '%s'.", log_level)
        return logger

    # -----------------------------------------------------------------------
    # Extension Loading
    # -----------------------------------------------------------------------
    async def _load_extensions(self) -> None:
        """Dynamically load all configured extensions (cogs).

        Iterates over the ``extensions.paths`` list in the configuration
        and attempts to load each one via :meth:`discord.ext.commands.Bot.load_extension`.
        Warnings are logged for extensions that fail to load, but startup
        continues so that the bot remains operational.

        Raises:
            ExtensionLoadError: If ``extensions.auto_load`` is ``True`` and
                at least one extension fails to load. This behavior can be
                disabled by setting ``extensions.auto_load`` to ``False``.

        """
        ext_config: dict[str, Any] = self.config.get("extensions", {})
        auto_load: bool = ext_config.get("auto_load", True)
        ext_paths: list[str] = ext_config.get("paths", [])

        if not ext_paths:
            self.logger.info("No extensions configured for auto-loading.")
            return

        self.logger.info("Loading %d extension(s)...", len(ext_paths))
        failed: list[str] = []

        for ext in ext_paths:
            try:
                await self.load_extension(ext)
                self.logger.info("Extension loaded: '%s'", ext)
            except commands.ExtensionNotFound:
                self.logger.warning("Extension not found: '%s'", ext)
                failed.append(ext)
            except commands.ExtensionAlreadyLoaded:
                self.logger.debug("Extension already loaded: '%s'", ext)
            except commands.NoEntryPointError:
                self.logger.warning("Extension missing setup function: '%s'", ext)
                failed.append(ext)
            except commands.ExtensionFailed as exc:
                self.logger.error(
                    "Extension '%s' failed to load: %s", ext, exc.original
                )
                failed.append(ext)

        if failed and auto_load:
            raise ExtensionLoadError(
                f"Failed to load {len(failed)} extension(s): {', '.join(failed)}"
            )

        self.logger.info(
            "Extension loading complete. %d loaded, %d failed.",
            len(ext_paths) - len(failed),
            len(failed),
        )

    # -----------------------------------------------------------------------
    # Event Handlers
    # -----------------------------------------------------------------------
    async def on_ready(self) -> None:
        """Handle the Discord ``READY`` event.

        Called once when the bot has successfully connected to Discord and
        is ready to process events. Logs connection details and sets the
        bot's presence activity if configured.

        """
        self.logger.info("-" * 50)
        self.logger.info("Bot is online and ready!")
        self.logger.info("Logged in as: %s (ID: %d)", self.user, self.user.id)
        self.logger.info("Connected to %d guild(s).", len(self.guilds))
        self.logger.info("discord.py version: %s", discord.__version__)
        self.logger.info("-" * 50)

        # Set activity if configured
        bot_config: dict[str, Any] = self.config.get("bot", {})
        activity_config: dict[str, str] | None = bot_config.get("activity")
        if activity_config:
            activity_type_str: str = activity_config.get("type", "playing").lower()
            activity_text: str = activity_config.get("text", "")

            activity_type_map: dict[str, discord.ActivityType] = {
                "playing": discord.ActivityType.playing,
                "streaming": discord.ActivityType.streaming,
                "listening": discord.ActivityType.listening,
                "watching": discord.ActivityType.watching,
                "competing": discord.ActivityType.competing,
            }
            activity_type = activity_type_map.get(
                activity_type_str, discord.ActivityType.playing
            )

            activity = discord.Activity(type=activity_type, name=activity_text)
            await self.change_presence(activity=activity)
            self.logger.info("Presence set: %s %s", activity_type_str.title(), activity_text)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        """Handle uncaught exceptions in event handlers.

        Logs the exception and suppresses it to prevent the bot from crashing.
        In a future version, this may also report errors to a monitoring service.

        Args:
            event_method: The name of the event handler that raised the error.
            *args: Positional arguments passed to the event handler.
            **kwargs: Keyword arguments passed to the event handler.

        """
        self.logger.exception("Unhandled exception in event '%s'", event_method)

    # -----------------------------------------------------------------------
    # Startup & Shutdown
    # -----------------------------------------------------------------------
    async def setup_hook(self) -> None:
        """Perform asynchronous setup before the bot connects to Discord.

        This method is called automatically by discord.py during the login
        process. It loads extensions and registers signal handlers for
        graceful shutdown.

        """
        self.logger.info("Running setup hook...")

        # Load extensions
        try:
            await self._load_extensions()
        except ExtensionLoadError:
            self.logger.exception("Extension loading failed during setup.")
            raise

        # Register signal handlers for graceful shutdown (Unix-like systems)
        try:
            loop = asyncio.get_running_loop()
            for sig in (signal.SIGINT, signal.SIGTERM):
                loop.add_signal_handler(sig, lambda s=sig: asyncio.create_task(self._signal_handler(s)))
            self.logger.debug("Signal handlers registered for SIGINT and SIGTERM.")
        except (ValueError, OSError, NotImplementedError):
            # Windows or environments where add_signal_handler is unavailable
            self.logger.debug("Signal handlers not available on this platform.")

        self.logger.info("Setup hook completed.")

    async def _signal_handler(self, sig: signal.Signals) -> None:
        """Handle OS signals for graceful shutdown.

        Args:
            sig: The signal that was received (e.g., ``SIGINT``, ``SIGTERM``).

        """
        self.logger.info("Received signal %s. Initiating graceful shutdown...", sig.name)
        self._shutdown_event.set()
        await self.close()

    async def start(self) -> None:
        """Start the bot and block until it disconnects.

        This is the primary entry point for running the bot. It retrieves
        the bot token from the configuration and delegates to
        :meth:`discord.ext.commands.Bot.start`.

        Raises:
            ConfigurationError: If the bot token is missing or invalid.
            discord.LoginFailure: If authentication with Discord fails.

        """
        token: str = self.config["bot"]["token"]
        if token in ("YOUR_DISCORD_BOT_TOKEN_HERE", "", None):
            raise ConfigurationError(
                "Invalid bot token. Please set a valid token in config.json."
            )

        self.logger.info("Starting ModerationBot v%s...", __import__("moderation").__version__)
        await super().start(token)

    async def close(self) -> None:
        """Gracefully shut down the bot.

        Performs cleanup operations before disconnecting from Discord.
        This method is called automatically on signal reception or can be
        invoked manually.

        """
        self.logger.info("Shutting down ModerationBot...")

        # Perform any additional cleanup here (e.g., database connections)
        # Future versions will close database pools and flush caches here.

        await super().close()
        self.logger.info("Bot disconnected. Goodbye!")

    def run(self) -> None:
        """Run the bot using the synchronous asyncio event loop.

        This is a convenience wrapper around :meth:`start` for users who
        prefer a blocking call. It handles the asyncio boilerplate.

        Example::

            bot = ModerationBot()
            bot.run()

        """
        try:
            asyncio.run(self.start())
        except KeyboardInterrupt:
            self.logger.info("Keyboard interrupt received. Exiting.")
        except ConfigurationError as exc:
            self.logger.critical("Configuration error: %s", exc)
            sys.exit(1)
        except discord.LoginFailure as exc:
            self.logger.critical("Discord login failed: %s", exc)
            sys.exit(1)
        except Exception as exc:
            self.logger.critical("Fatal error during bot execution: %s", exc)
            sys.exit(1)


# ---------------------------------------------------------------------------
# Module Entry Point
# ---------------------------------------------------------------------------
def main() -> None:
    """CLI entry point for the moderation bot.

    Instantiates :class:`ModerationBot` and runs it. This function is
    invoked when the module is executed directly::

        $ python -m moderation

    """
    bot = ModerationBot()
    bot.run()


if __name__ == "__main__":
    main()
      
