"""Error handling event listeners for the moderation module.

This module implements global error handlers for command errors, check
failures, and unhandled exceptions. It provides consistent user-facing
error messages and logging across all commands.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from moderation.constants import EMBED_COLOR_ERROR, EMBED_COLOR_WARNING
from moderation.exceptions.base import ModerationError
from moderation.logger import get_logger

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


def _create_error_embed(title: str, description: str) -> discord.Embed:
    """Create a standardized error embed.

    Args:
        title: The embed title.
        description: The embed description.

    Returns:
        A configured :class:`discord.Embed` instance.

    """
    return discord.Embed(
        title=title,
        description=description,
        color=EMBED_COLOR_ERROR,
    )


class ErrorEvents(commands.Cog):
    """Global error handling event listeners.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        logger: A logger for this cog.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the ErrorEvents cog.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self.logger = get_logger(f"{__name__}.ErrorEvents")

    # ===================================================================
    # Command Error Handler
    # ===================================================================
    @commands.Cog.listener()
    async def on_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Handle errors raised by prefix commands.

        Args:
            ctx: The command context.
            error: The error that was raised.

        """
        if hasattr(ctx.command, "on_error"):
            # Command has local error handler, skip global
            return

        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.DisabledCommand):
            embed = _create_error_embed(
                "Command Disabled",
                "This command is currently disabled.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.NoPrivateMessage):
            embed = _create_error_embed(
                "Server Only",
                "This command can only be used in a server.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.PrivateMessageOnly):
            embed = _create_error_embed(
                "DMs Only",
                "This command can only be used in direct messages.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.NotOwner):
            embed = _create_error_embed(
                "Owner Only",
                "This command is restricted to bot owners.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = _create_error_embed(
                "Missing Permissions",
                f"You need the following permissions: {perms}",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = _create_error_embed(
                "Bot Missing Permissions",
                f"I need the following permissions: {perms}",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRole):
            embed = _create_error_embed(
                "Missing Role",
                f"You need the role `{error.missing_role}` to use this command.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BotMissingRole):
            embed = _create_error_embed(
                "Bot Missing Role",
                f"I need the role `{error.missing_role}` to run this command.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingAnyRole):
            roles = ", ".join(f"`{r}`" for r in error.missing_roles)
            embed = _create_error_embed(
                "Missing Role",
                f"You need one of the following roles: {roles}",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.NSFWChannelRequired):
            embed = _create_error_embed(
                "NSFW Channel Required",
                "This command can only be used in an NSFW channel.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CheckFailure):
            embed = _create_error_embed(
                "Check Failed",
                "You do not meet the requirements to use this command.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Cooldown",
                description=f"Please wait `{error.retry_after:.1f}` seconds before using this command again.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MaxConcurrencyReached):
            embed = _create_error_embed(
                "Concurrency Limit",
                f"This command can only be used `{error.number}` time(s) per `{error.per.name}`.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed = _create_error_embed(
                "Missing Argument",
                f"Missing required argument: `{error.param.name}`",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.TooManyArguments):
            embed = _create_error_embed(
                "Too Many Arguments",
                "You provided too many arguments for this command.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadArgument):
            embed = _create_error_embed(
                "Invalid Argument",
                str(error),
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadUnionArgument):
            embed = _create_error_embed(
                "Invalid Argument",
                f"Could not convert `{error.param.name}` to any of the expected types.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.BadLiteralArgument):
            embed = _create_error_embed(
                "Invalid Argument",
                f"Expected one of: {', '.join(f'`{l}`' for l in error.literals)}",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.RangeError):
            embed = _create_error_embed(
                "Invalid Value",
                f"Value must be between `{error.minimum}` and `{error.maximum}`.",
            )
            await ctx.send(embed=embed)
            return

        if isinstance(error, commands.ArgumentParsingError):
            embed = _create_error_embed(
                "Argument Error",
                str(error),
            )
            await ctx.send(embed=embed)
            return

        # Handle our custom exceptions
        if isinstance(error, ModerationError):
            embed = _create_error_embed(
                "Moderation Error",
                str(error),
            )
            await ctx.send(embed=embed)
            return

        # Unhandled errors
        self.logger.exception(
            "Unhandled error in command %s by %s (%d): %s",
            ctx.command.name if ctx.command else "unknown",
            ctx.author,
            ctx.author.id,
            error,
        )

        embed = _create_error_embed(
            "Unexpected Error",
            "An unexpected error occurred. Please try again later.",
        )
        await ctx.send(embed=embed)

    # ===================================================================
    # App Command Error Handler
    # ===================================================================
    @commands.Cog.listener()
    async def on_application_command_error(
        self,
        interaction: discord.Interaction,
        error: discord.app_commands.AppCommandError,
    ) -> None:
        """Handle errors raised by application (slash) commands.

        Args:
            interaction: The interaction that triggered the error.
            error: The error that was raised.

        """
        if isinstance(error, discord.app_commands.CommandNotFound):
            return

        if isinstance(error, discord.app_commands.MissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = _create_error_embed(
                "Missing Permissions",
                f"You need the following permissions: {perms}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(error, discord.app_commands.BotMissingPermissions):
            perms = ", ".join(f"`{p}`" for p in error.missing_permissions)
            embed = _create_error_embed(
                "Bot Missing Permissions",
                f"I need the following permissions: {perms}",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(error, discord.app_commands.NoPrivateMessage):
            embed = _create_error_embed(
                "Server Only",
                "This command can only be used in a server.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(error, discord.app_commands.CheckFailure):
            embed = _create_error_embed(
                "Check Failed",
                "You do not meet the requirements to use this command.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(error, discord.app_commands.CommandOnCooldown):
            embed = discord.Embed(
                title="Cooldown",
                description=f"Please wait `{error.retry_after:.1f}` seconds before using this command again.",
                color=EMBED_COLOR_WARNING,
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        if isinstance(error, discord.app_commands.TransformerError):
            embed = _create_error_embed(
                "Invalid Input",
                f"Could not convert `{error.value}` to the expected type.",
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Handle our custom exceptions
        if isinstance(error, ModerationError):
            embed = _create_error_embed(
                "Moderation Error",
                str(error),
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return

        # Unhandled errors
        self.logger.exception(
            "Unhandled error in app command %s by %s (%d): %s",
            interaction.command.name if interaction.command else "unknown",
            interaction.user,
            interaction.user.id,
            error,
        )

        embed = _create_error_embed(
            "Unexpected Error",
            "An unexpected error occurred. Please try again later.",
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)

    # ===================================================================
    # Interaction Error Handler
    # ===================================================================
    @commands.Cog.listener()
    async def on_interaction_error(
        self,
        interaction: discord.Interaction,
        error: Exception,
    ) -> None:
        """Handle unhandled interaction errors.

        Args:
            interaction: The interaction that triggered the error.
            error: The error that was raised.

        """
        self.logger.exception(
            "Unhandled interaction error by %s (%d): %s",
            interaction.user,
            interaction.user.id,
            error,
        )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
async def setup(bot: ModerationBot) -> None:
    """Add the ErrorEvents cog to the bot.

    Args:
        bot: The bot instance.

    """
    await bot.add_cog(ErrorEvents(bot))
