"""Owner-only commands for the moderation module.

This module implements commands restricted to bot owners, including
global evaluation, extension management, and administrative utilities.

"""

from __future__ import annotations

import asyncio
import importlib
import io
import sys
import textwrap
import traceback
from typing import TYPE_CHECKING, Any

import discord
from discord.ext import commands

from moderation.constants import EMBED_COLOR_ERROR, EMBED_COLOR_INFO, EMBED_COLOR_SUCCESS
from moderation.logger import get_logger

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


def _create_embed(
    title: str,
    description: str,
    color: int = EMBED_COLOR_INFO,
) -> discord.Embed:
    """Create a standardized embed for command responses.

    Args:
        title: The embed title.
        description: The embed description.
        color: The embed color. Defaults to info blue.

    Returns:
        A configured :class:`discord.Embed` instance.

    """
    return discord.Embed(
        title=title,
        description=description,
        color=color,
    )


class OwnerCog(commands.Cog):
    """Owner-only administrative commands.

    These commands are restricted to the bot owners configured in
    ``config.json`` and provide tools for debugging, maintenance,
    and runtime management.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        logger: A logger for this cog.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the OwnerCog.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self.logger = get_logger(f"{__name__}.OwnerCog")

    async def cog_check(self, ctx: commands.Context) -> bool:
        """Restrict all commands in this cog to bot owners.

        Args:
            ctx: The command context.

        Returns:
            True if the user is a bot owner, False otherwise.

        """
        owner_ids: list[int] = self.bot.config.get("bot", {}).get("owner_ids", [])
        return ctx.author.id in owner_ids

    # ===================================================================
    # Eval
    # ===================================================================
    @commands.command(name="eval", hidden=True)
    async def _eval(self, ctx: commands.Context, *, code: str) -> None:
        """Execute arbitrary Python code. Owner only.

        This command provides a REPL-like interface for debugging and
        administrative tasks. Use with extreme caution.

        Args:
            ctx: The command context.
            code: The Python code to execute.

        """
        env = {
            "bot": self.bot,
            "ctx": ctx,
            "discord": discord,
            "commands": commands,
            "asyncio": asyncio,
            "importlib": importlib,
            "__import__": __import__,
        }

        stdout = io.StringIO()

        code = code.strip()
        if code.startswith("```") and code.endswith("```"):
            code = "\n".join(code.split("\n")[1:-1])
        code = code.strip("`")

        wrapped = f"async def _eval_expr():\n{textwrap.indent(code, '    ')}"

        try:
            exec(wrapped, env)  # noqa: S102
        except SyntaxError as exc:
            embed = _create_embed(
                title="Syntax Error",
                description=f"```py\n{traceback.format_exc()}\n```",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        func = env["_eval_expr"]

        try:
            with contextlib.redirect_stdout(stdout):
                result = await func()
        except Exception:
            embed = _create_embed(
                title="Runtime Error",
                description=f"```py\n{traceback.format_exc()}\n```",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        output = stdout.getvalue()

        embed = _create_embed(
            title="Eval Result",
            color=EMBED_COLOR_SUCCESS,
        )

        if result is not None:
            embed.add_field(name="Return Value", value=f"```py\n{result!r}\n```", inline=False)

        if output:
            embed.add_field(name="Stdout", value=f"```\n{output}\n```", inline=False)

        if not embed.fields:
            embed.description = "Executed successfully with no output."

        await ctx.send(embed=embed)

    # ===================================================================
    # Load Extension
    # ===================================================================
    @commands.command(name="load", hidden=True)
    async def load_extension(self, ctx: commands.Context, extension: str) -> None:
        """Load a bot extension dynamically. Owner only.

        Args:
            ctx: The command context.
            extension: The dotted module path of the extension to load.

        """
        try:
            await self.bot.load_extension(extension)
        except commands.ExtensionNotFound:
            embed = _create_embed(
                title="Extension Not Found",
                description=f"Extension `{extension}` was not found.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return
        except commands.ExtensionAlreadyLoaded:
            embed = _create_embed(
                title="Already Loaded",
                description=f"Extension `{extension}` is already loaded.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return
        except commands.ExtensionFailed as exc:
            embed = _create_embed(
                title="Extension Failed",
                description=f"Extension `{extension}` failed to load:\n```py\n{exc}\n```",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        embed = _create_embed(
            title="Extension Loaded",
            description=f"Extension `{extension}` loaded successfully.",
            color=EMBED_COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        self.logger.info("Owner %s loaded extension '%s'.", ctx.author, extension)

    # ===================================================================
    # Unload Extension
    # ===================================================================
    @commands.command(name="unload", hidden=True)
    async def unload_extension(self, ctx: commands.Context, extension: str) -> None:
        """Unload a bot extension dynamically. Owner only.

        Args:
            ctx: The command context.
            extension: The dotted module path of the extension to unload.

        """
        try:
            await self.bot.unload_extension(extension)
        except commands.ExtensionNotLoaded:
            embed = _create_embed(
                title="Not Loaded",
                description=f"Extension `{extension}` is not loaded.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        embed = _create_embed(
            title="Extension Unloaded",
            description=f"Extension `{extension}` unloaded successfully.",
            color=EMBED_COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        self.logger.info("Owner %s unloaded extension '%s'.", ctx.author, extension)

    # ===================================================================
    # Reload Extension
    # ===================================================================
    @commands.command(name="reload", hidden=True)
    async def reload_extension(self, ctx: commands.Context, extension: str) -> None:
        """Reload a bot extension dynamically. Owner only.

        Args:
            ctx: The command context.
            extension: The dotted module path of the extension to reload.

        """
        try:
            await self.bot.reload_extension(extension)
        except commands.ExtensionNotLoaded:
            embed = _create_embed(
                title="Not Loaded",
                description=f"Extension `{extension}` is not loaded.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return
        except commands.ExtensionNotFound:
            embed = _create_embed(
                title="Extension Not Found",
                description=f"Extension `{extension}` was not found.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return
        except commands.ExtensionFailed as exc:
            embed = _create_embed(
                title="Extension Failed",
                description=f"Extension `{extension}` failed to reload:\n```py\n{exc}\n```",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed)
            return

        embed = _create_embed(
            title="Extension Reloaded",
            description=f"Extension `{extension}` reloaded successfully.",
            color=EMBED_COLOR_SUCCESS,
        )
        await ctx.send(embed=embed)
        self.logger.info("Owner %s reloaded extension '%s'.", ctx.author, extension)

    # ===================================================================
    # Shutdown
    # ===================================================================
    @commands.command(name="shutdown", hidden=True)
    async def shutdown(self, ctx: commands.Context) -> None:
        """Gracefully shut down the bot. Owner only.

        Args:
            ctx: The command context.

        """
        embed = _create_embed(
            title="Shutting Down",
            description="The bot is shutting down...",
            color=EMBED_COLOR_INFO,
        )
        await ctx.send(embed=embed)
        self.logger.info("Owner %s initiated shutdown.", ctx.author)
        await self.bot.close()


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
async def setup(bot: ModerationBot) -> None:
    """Add the OwnerCog to the bot.

    Args:
        bot: The bot instance.

    """
    await bot.add_cog(OwnerCog(bot))
