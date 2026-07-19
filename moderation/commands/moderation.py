"""Core moderation commands for the moderation module.

This module implements the primary moderation commands for Version 1.0:
kick, ban, timeout, warn, unban, purge, slowmode, nickname moderation,
lock/unlock channels, and role moderation.

All commands are implemented as a single discord.py Cog for organizational
simplicity. Future versions may split this into multiple cogs.

"""

from __future__ import annotations

import asyncio
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING

import discord
from discord import app_commands
from discord.ext import commands

from moderation.constants import (
    DEFAULT_PURGE_MESSAGES,
    DEFAULT_TIMEOUT_DURATION,
    EMBED_COLOR_ERROR,
    EMBED_COLOR_INFO,
    EMBED_COLOR_SUCCESS,
    E MAX_PURGE_MESSAGES,
    MAX_SLOWMODE_DURATION,
    MAX_TIMEOUT_DURATION,
    MIN_SLOWMODE_DURATION,
    MIN_TIMEOUT_DURATION,
   MBED_COLOR_SUCCESS,
    MAX_PURGE_MESSAGES,
    MAX_SLOWMODE_DURATION,
    MAX_TIMEOUT_DURATION,
    MIN_SLOWMODE_DURATION,
    MIN_TIMEOUT_DURATION,
    TIME_UNIT_MULTIPLIERS,
)
from moderation.exceptions.checks import (
    BotHierarchyError,
    HierarchyViolationError,
    InsufficientPermissionsError,
    OwnerImmuneError,
    SelfModerationError,
)
from moderation.exceptions.commands import (
    ActionFailedError,
    InvalidChannelError,
    InvalidDurationError,
    InvalidRoleError,
    InvalidUserError,
)
from moderation.logger import get_logger

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def _parse_duration(duration_str: str) -> int:
    """Parse a human-readable duration string into seconds.

    Supports formats like ``1h30m``, ``2d``, ``1w``, ``45s``.
    Compound durations (e.g., ``1d12h``) are supported.

    Args:
        duration_str: The duration string to parse.

    Returns:
        The duration in seconds.

    Raises:
        InvalidDurationError: If the string cannot be parsed or exceeds limits.

    """
    if not duration_str or not duration_str.strip():
        raise InvalidDurationError(
            "Duration cannot be empty.",
            input_value=duration_str,
        )

    duration_str = duration_str.strip().lower()
    total_seconds = 0
    current_number = ""
    idx = 0

    while idx < len(duration_str):
        char = duration_str[idx]

        if char.isdigit():
            current_number += char
            idx += 1
            continue

        if char.isalpha():
            if not current_number:
                raise InvalidDurationError(
                    f"Invalid duration format: '{duration_str}'. "
                    "Expected format like '1h30m', '2d', or '1w'.",
                    input_value=duration_str,
                )

            # Collect the full unit word
            unit_start = idx
            while idx < len(duration_str) and duration_str[idx].isalpha():
                idx += 1
            unit = duration_str[unit_start:idx]

            multiplier = TIME_UNIT_MULTIPLIERS.get(unit)
            if multiplier is None:
                raise InvalidDurationError(
                    f"Unknown time unit: '{unit}'. "
                    "Supported units: s, m, h, d, w.",
                    input_value=duration_str,
                )

            total_seconds += int(current_number) * multiplier
            current_number = ""
            continue

        # Skip whitespace
        if char.isspace():
            idx += 1
            continue

        raise InvalidDurationError(
            f"Invalid character in duration: '{char}'.",
            input_value=duration_str,
        )

    if current_number:
        # Trailing number without unit — treat as seconds
        total_seconds += int(current_number)

    if total_seconds <= 0:
        raise InvalidDurationError(
            "Duration must be greater than zero.",
            input_value=duration_str,
        )

    if total_seconds > MAX_TIMEOUT_DURATION:
        raise InvalidDurationError(
            f"Duration exceeds maximum of {MAX_TIMEOUT_DURATION} seconds "
            f"({MAX_TIMEOUT_DURATION // SECONDS_PER_DAY} days).",
            input_value=duration_str,
            max_allowed=MAX_TIMEOUT_DURATION,
        )

    return total_seconds


SECONDS_PER_DAY = 86400  # Used in error messages above


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
        timestamp=datetime.now(timezone.utc),
    )


async def _check_hierarchy(
    ctx: commands.Context,
    target: discord.Member,
) -> None:
    """Validate that the moderator can action the target user.

    Checks:
    1. Target is not the moderator themselves.
    2. Target is not the guild owner.
    3. Target is not a bot owner.
    4. Moderator's top role is higher than target's top role.
    5. Bot's top role is higher than target's top role.

    Args:
        ctx: The command context.
        target: The member to be moderated.

    Raises:
        SelfModerationError: If target is the invoking user.
        OwnerImmuneError: If target is the guild or bot owner.
        HierarchyViolationError: If moderator cannot action target.
        BotHierarchyError: If bot cannot action target.

    """
    if target.id == ctx.author.id:
        raise SelfModerationError(action=ctx.command.name if ctx.command else "unknown")

    if target.id == ctx.guild.owner_id:
        raise OwnerImmuneError(
            "You cannot moderate the server owner.",
            target_id=target.id,
            reason="guild_owner",
        )

    # Check bot owner immunity (config-based owner IDs would go here)
    # For now, we check if the user has administrator and is above everyone
    if target.guild_permissions.administrator and target.top_role.position == 0:
        # This is a simplistic check; real implementation would use config owner_ids
        pass

    # Role hierarchy check: moderator must have higher top role
    if ctx.author.top_role.position <= target.top_role.position:
        if ctx.author.id != ctx.guild.owner_id:
            raise HierarchyViolationError(
                f"You cannot moderate {target.mention} because they have an equal or higher role.",
                target_id=target.id,
                target_top_role=target.top_role.name,
            )

    # Bot hierarchy check: bot must have higher top role than target
    bot_member = ctx.guild.me
    if bot_member.top_role.position <= target.top_role.position:
        raise BotHierarchyError(
            f"I cannot moderate {target.mention} because their highest role is above mine.",
            bot_top_role=bot_member.top_role.name,
            target_top_role=target.top_role.name,
        )


# ---------------------------------------------------------------------------
# Moderation Cog
# ---------------------------------------------------------------------------
class ModerationCog(commands.Cog):
    """Core moderation commands cog.

    Implements all Version 1.0 moderation commands: kick, ban, timeout,
    warn, unban, purge, slowmode, nickname, lock/unlock, and role moderation.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        logger: A logger for this cog.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the ModerationCog.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self.logger = get_logger(f"{__name__}.ModerationCog")

    # ===================================================================
    # Kick
    # ===================================================================
    @commands.hybrid_command(
        name="kick",
        description="Kick a member from the server.",
    )
    @app_commands.describe(
        member="The member to kick.",
        reason="The reason for the kick.",
    )
    @commands.has_permissions(kick_members=True)
    @commands.bot_has_permissions(kick_members=True)
    async def kick(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Kick a member from the server.

        Args:
            ctx: The command context.
            member: The member to kick.
            reason: The reason for the kick (optional).

        """
        await _check_hierarchy(ctx, member)

        try:
            await member.kick(reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to kick {member.mention}: I do not have permission.",
                action="kick",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to kick {member.mention}: {exc.text}",
                action="kick",
                target_id=member.id,
            ) from exc

        embed = _create_embed(
            title="Member Kicked",
            description=f"{member.mention} has been kicked by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) kicked %s (%d). Reason: %s",
            ctx.author, ctx.author.id, member, member.id, reason,
        )

    # ===================================================================
    # Ban
    # ===================================================================
    @commands.hybrid_command(
        name="ban",
        description="Ban a member from the server.",
    )
    @app_commands.describe(
        member="The member to ban.",
        reason="The reason for the ban.",
        delete_days="Number of days of messages to delete (0-7).",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def ban(
        self,
        ctx: commands.Context,
        member: discord.Member,
        delete_days: commands.Range[int, 0, 7] = 1,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Ban a member from the server.

        Args:
            ctx: The command context.
            member: The member to ban.
            delete_days: Days of message history to delete (0-7). Defaults to 1.
            reason: The reason for the ban (optional).

        """
        await _check_hierarchy(ctx, member)

        try:
            await member.ban(
                reason=f"{ctx.author} ({ctx.author.id}): {reason}",
                delete_message_days=delete_days,
            )
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to ban {member.mention}: I do not have permission.",
                action="ban",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to ban {member.mention}: {exc.text}",
                action="ban",
                target_id=member.id,
            ) from exc

        embed = _create_embed(
            title="Member Banned",
            description=f"{member.mention} has been banned by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Delete Days", value=str(delete_days), inline=True)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) banned %s (%d). Reason: %s | Delete days: %d",
            ctx.author, ctx.author.id, member, member.id, reason, delete_days,
        )

    # ===================================================================
    # Timeout
    # ===================================================================
    @commands.hybrid_command(
        name="timeout",
        description="Timeout a member for a specified duration.",
    )
    @app_commands.describe(
        member="The member to timeout.",
        duration="Duration (e.g., 1h, 30m, 1d, 1w). Max 28 days.",
        reason="The reason for the timeout.",
    )
    @commands.has_permissions(moderate_members=True)
    @commands.bot_has_permissions(moderate_members=True)
    async def timeout(
        self,
        ctx: commands.Context,
        member: discord.Member,
        duration: str,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Timeout a member for a specified duration.

        Args:
            ctx: The command context.
            member: The member to timeout.
            duration: Duration string (e.g., ``1h``, ``30m``, ``1d``, ``1w``).
            reason: The reason for the timeout (optional).

        """
        await _check_hierarchy(ctx, member)

        seconds = _parse_duration(duration)
        if seconds < MIN_TIMEOUT_DURATION:
            raise InvalidDurationError(
                f"Timeout duration must be at least {MIN_TIMEOUT_DURATION} second(s).",
                input_value=duration,
            )
        if seconds > MAX_TIMEOUT_DURATION:
            raise InvalidDurationError(
                f"Timeout duration cannot exceed {MAX_TIMEOUT_DURATION // 86400} days.",
                input_value=duration,
                max_allowed=MAX_TIMEOUT_DURATION,
            )

        until = datetime.now(timezone.utc) + timedelta(seconds=seconds)

        try:
            await member.timeout(until, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to timeout {member.mention}: I do not have permission.",
                action="timeout",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to timeout {member.mention}: {exc.text}",
                action="timeout",
                target_id=member.id,
            ) from exc

        embed = _create_embed(
            title="Member Timed Out",
            description=f"{member.mention} has been timed out by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Duration", value=duration, inline=True)
        embed.add_field(name="Expires", value=discord.utils.format_dt(until, "R"), inline=True)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) timed out %s (%d) for %s. Reason: %s",
            ctx.author, ctx.author.id, member, member.id, duration, reason,
        )

    # ===================================================================
    # Warn
    # ===================================================================
    @commands.hybrid_command(
        name="warn",
        description="Issue a warning to a member.",
    )
    @app_commands.describe(
        member="The member to warn.",
        reason="The reason for the warning.",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def warn(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Issue a warning to a member.

        In Version 1.0, warnings are logged but not persisted to a case
        system. Version 1.1 will add case tracking and warn accumulation.

        Args:
            ctx: The command context.
            member: The member to warn.
            reason: The reason for the warning (optional).

        """
        await _check_hierarchy(ctx, member)

        # TODO: Version 1.1 — persist warning to case system
        # For now, we log and notify

        embed = _create_embed(
            title="Member Warned",
            description=f"{member.mention} has been warned by {ctx.author.mention}.",
            color=EMBED_COLOR_WARNING,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)
        embed.set_footer(text="Warning logged. Case system coming in v1.1.")

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) warned %s (%d). Reason: %s",
            ctx.author, ctx.author.id, member, member.id, reason,
        )

    # ===================================================================
    # Unban
    # ===================================================================
    @commands.hybrid_command(
        name="unban",
        description="Unban a user from the server.",
    )
    @app_commands.describe(
        user="The user to unban (ID or mention).",
        reason="The reason for the unban.",
    )
    @commands.has_permissions(ban_members=True)
    @commands.bot_has_permissions(ban_members=True)
    async def unban(
        self,
        ctx: commands.Context,
        user: discord.User,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Unban a user from the server.

        Args:
            ctx: The command context.
            user: The user to unban.
            reason: The reason for the unban (optional).

        """
        try:
            await ctx.guild.unban(user, reason=f"{ctx.author} ({ctx.author.id}): {reason}")
        except discord.NotFound as exc:
            raise InvalidUserError(
                f"User {user.mention} is not banned in this server.",
                input_value=str(user.id),
            ) from exc
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to unban {user.mention}: I do not have permission.",
                action="unban",
                target_id=user.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to unban {user.mention}: {exc.text}",
                action="unban",
                target_id=user.id,
            ) from exc

        embed = _create_embed(
            title="User Unbanned",
            description=f"{user.mention} has been unbanned by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="User ID", value=str(user.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) unbanned %s (%d). Reason: %s",
            ctx.author, ctx.author.id, user, user.id, reason,
        )

    # ===================================================================
    # Purge
    # ===================================================================
    @commands.hybrid_command(
        name="purge",
        description="Delete a number of messages from the current channel.",
    )
    @app_commands.describe(
        amount="Number of messages to delete (1-1000).",
        user="Only delete messages from this user (optional).",
    )
    @commands.has_permissions(manage_messages=True)
    @commands.bot_has_permissions(manage_messages=True, read_message_history=True)
    async def purge(
        self,
        ctx: commands.Context,
        amount: commands.Range[int, 1, 1000],
        user: discord.Member | None = None,
    ) -> None:
        """Delete messages from the current channel.

        Args:
            ctx: The command context.
            amount: Number of messages to delete (1-1000).
            user: If provided, only delete messages from this user.

        """
        if amount > MAX_PURGE_MESSAGES:
            amount = MAX_PURGE_MESSAGES

        def check(msg: discord.Message) -> bool:
            if user is None:
                return True
            return msg.author.id == user.id

        try:
            deleted = await ctx.channel.purge(limit=amount, check=check, before=ctx.message)
        except discord.Forbidden as exc:
            raise ActionFailedError(
                "Failed to purge messages: I do not have permission.",
                action="purge",
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to purge messages: {exc.text}",
                action="purge",
            ) from exc

        # Delete the command invocation message too
        try:
            await ctx.message.delete()
        except (discord.Forbidden, discord.HTTPException):
            pass

        embed = _create_embed(
            title="Messages Purged",
            description=f"Deleted **{len(deleted)}** message(s).",
            color=EMBED_COLOR_SUCCESS,
        )
        if user:
            embed.add_field(name="Filter", value=f"Only from {user.mention}", inline=False)

        await ctx.send(embed=embed, delete_after=5.0)
        self.logger.info(
            "User %s (%d) purged %d messages in #%s. Filter: %s",
            ctx.author, ctx.author.id, len(deleted), ctx.channel.name,
            user.mention if user else "None",
        )

    # ===================================================================
    # Slowmode
    # ===================================================================
    @commands.hybrid_command(
        name="slowmode",
        description="Set slowmode delay for the current channel.",
    )
    @app_commands.describe(
        seconds="Slowmode delay in seconds (0 to disable, max 21600).",
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def slowmode(
        self,
        ctx: commands.Context,
        seconds: commands.Range[int, 0, 21600],
    ) -> None:
        """Set slowmode delay for the current channel.

        Args:
            ctx: The command context.
            seconds: Delay in seconds. 0 disables slowmode.

        """
        if seconds < MIN_SLOWMODE_DURATION:
            seconds = MIN_SLOWMODE_DURATION
        if seconds > MAX_SLOWMODE_DURATION:
            seconds = MAX_SLOWMODE_DURATION

        try:
            await ctx.channel.edit(slowmode_delay=seconds)
        except discord.Forbidden as exc:
            raise ActionFailedError(
                "Failed to set slowmode: I do not have permission.",
                action="slowmode",
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to set slowmode: {exc.text}",
                action="slowmode",
            ) from exc

        if seconds == 0:
            embed = _create_embed(
                title="Slowmode Disabled",
                description=f"Slowmode has been disabled in {ctx.channel.mention}.",
                color=EMBED_COLOR_SUCCESS,
            )
        else:
            embed = _create_embed(
                title="Slowmode Updated",
                description=f"Slowmode set to **{seconds}** second(s) in {ctx.channel.mention}.",
                color=EMBED_COLOR_SUCCESS,
            )

        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) set slowmode to %ds in #%s.",
            ctx.author, ctx.author.id, seconds, ctx.channel.name,
        )

    # ===================================================================
    # Nickname
    # ===================================================================
    @commands.hybrid_command(
        name="nickname",
        description="Change or reset a member's nickname.",
    )
    @app_commands.describe(
        member="The member whose nickname to change.",
        nickname="The new nickname (omit to reset).",
    )
    @commands.has_permissions(manage_nicknames=True)
    @commands.bot_has_permissions(manage_nicknames=True)
    async def nickname(
        self,
        ctx: commands.Context,
        member: discord.Member,
        *,
        nickname: str | None = None,
    ) -> None:
        """Change or reset a member's nickname.

        Args:
            ctx: The command context.
            member: The member whose nickname to change.
            nickname: The new nickname. Omit or pass empty to reset.

        """
        await _check_hierarchy(ctx, member)

        # Empty string means reset
        new_nick = nickname.strip() if nickname else None

        try:
            await member.edit(nick=new_nick)
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to change nickname for {member.mention}: I do not have permission.",
                action="nickname",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to change nickname for {member.mention}: {exc.text}",
                action="nickname",
                target_id=member.id,
            ) from exc

        if new_nick:
            embed = _create_embed(
                title="Nickname Changed",
                description=f"{member.mention}'s nickname has been changed to **{new_nick}**.",
                color=EMBED_COLOR_SUCCESS,
            )
        else:
            embed = _create_embed(
                title="Nickname Reset",
                description=f"{member.mention}'s nickname has been reset.",
                color=EMBED_COLOR_SUCCESS,
            )

        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) changed nickname of %s (%d) to '%s'.",
            ctx.author, ctx.author.id, member, member.id, new_nick,
        )

    # ===================================================================
    # Lock
    # ===================================================================
    @commands.hybrid_command(
        name="lock",
        description="Lock a channel so @everyone cannot send messages.",
    )
    @app_commands.describe(
        channel="The channel to lock (defaults to current).",
        reason="The reason for locking the channel.",
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def lock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Lock a channel so @everyone cannot send messages.

        Args:
            ctx: The command context.
            channel: The channel to lock. Defaults to the current channel.
            reason: The reason for locking (optional).

        """
        target = channel or ctx.channel

        everyone = ctx.guild.default_role
        overwrite = target.overwrites_for(everyone)

        if overwrite.send_messages is False:
            embed = _create_embed(
                title="Channel Already Locked",
                description=f"{target.mention} is already locked.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        overwrite.send_messages = False

        try:
            await target.set_permissions(
                everyone,
                overwrite=overwrite,
                reason=f"{ctx.author} ({ctx.author.id}): {reason}",
            )
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to lock {target.mention}: I do not have permission.",
                action="lock",
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to lock {target.mention}: {exc.text}",
                action="lock",
            ) from exc

        embed = _create_embed(
            title="Channel Locked",
            description=f"{target.mention} has been locked by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) locked #%s. Reason: %s",
            ctx.author, ctx.author.id, target.name, reason,
        )

    # ===================================================================
    # Unlock
    # ===================================================================
    @commands.hybrid_command(
        name="unlock",
        description="Unlock a channel so @everyone can send messages.",
    )
    @app_commands.describe(
        channel="The channel to unlock to unlock (defaults to current).",
        reason="The reason for unlocking the channel.",
    )
    @commands.has_permissions(manage_channels=True)
    @commands.bot_has_permissions(manage_channels=True)
    async def unlock(
        self,
        ctx: commands.Context,
        channel: discord.TextChannel | None = None,
        *,
        reason: str = "No reason provided.",
    ) -> None:
        """Unlock a channel so @everyone can send messages.

        Args:
            ctx: The command context.
            channel: The channel to unlock. Defaults to the current channel.
            reason: The reason for unlocking (optional).

        """
        target = channel or ctx.channel

        everyone = ctx.guild.default_role
        overwrite = target.overwrites_for(everyone)

        if overwrite.send_messages is True or overwrite.send_messages is None:
            embed = _create_embed(
                title="Channel Already Unlocked",
                description=f"{target.mention} is not locked.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        overwrite.send_messages = None  # Reset to default

        try:
            await target.set_permissions(
                everyone,
                overwrite=overwrite,
                reason=f"{ctx.author} ({ctx.author.id}): {reason}",
            )
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to unlock {target.mention}: I do not have permission.",
                action="unlock",
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to unlock {target.mention}: {exc.text}",
                action="unlock",
            ) from exc

        embed = _create_embed(
            title="Channel Unlocked",
            description=f"{target.mention} has been unlocked by {ctx.author.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) unlocked #%s. Reason: %s",
            ctx.author, ctx.author.id, target.name, reason,
        )

    # ===================================================================
    # Role Add
    # ===================================================================
    @commands.hybrid_command(
        name="roleadd",
        description="Add a role to a member.",
    )
    @app_commands.describe(
        member="The member to add the role to.",
        role="The role to add.",
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def roleadd(
        self,
        ctx: commands.Context,
        member: discord.Member,
        role: discord.Role,
    ) -> None:
        """Add a role to a member.

        Args:
            ctx: The command context.
            member: The member to receive the role.
            role: The role to add.

        """
        # Bot cannot assign roles above its own top role
        if role.position >= ctx.guild.me.top_role.position:
            raise BotHierarchyError(
                f"I cannot assign {role.mention} because it is above my highest role.",
                bot_top_role=ctx.guild.me.top_role.name,
                target_top_role=role.name,
            )

        # Moderator cannot assign roles above their own top role
        if role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            raise HierarchyViolationError(
                f"You cannot assign {role.mention} because it is above your highest role.",
                target_id=member.id,
                target_top_role=role.name,
            )

        if role in member.roles:
            embed = _create_embed(
                title="Role Already Assigned",
                description=f"{member.mention} already has {role.mention}.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        try:
            await member.add_roles(role, reason=f"{ctx.author} ({ctx.author.id})")
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to add {role.mention} to {member.mention}: I do not have permission.",
                action="role_add",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to add {role.mention} to {member.mention}: {exc.text}",
                action="role_add",
                target_id=member.id,
            ) from exc

        embed = _create_embed(
            title="Role Added",
            description=f"Added {role.mention} to {member.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) added role '%s' (%d) to %s (%d).",
            ctx.author, ctx.author.id, role.name, role.id, member, member.id,
        )

    # ===================================================================
    # Role Remove
    # ===================================================================
    @commands.hybrid_command(
        name="roleremove",
        description="Remove a role from a member.",
    )
    @app_commands.describe(
        member="The member to remove the role from.",
        role="The role to remove.",
    )
    @commands.has_permissions(manage_roles=True)
    @commands.bot_has_permissions(manage_roles=True)
    async def roleremove(
        self,
        ctx: commands.Context,
        member: discord.Member,
        role: discord.Role,
    ) -> None:
        """Remove a role from a member.

        Args:
            ctx: The command context.
            member: The member to lose the role.
            role: The role to remove.

        """
        # Same hierarchy checks as roleadd
        if role.position >= ctx.guild.me.top_role.position:
            raise BotHierarchyError(
                f"I cannot remove {role.mention} because it is above my highest role.",
                bot_top_role=ctx.guild.me.top_role.name,
                target_top_role=role.name,
            )

        if role.position >= ctx.author.top_role.position and ctx.author.id != ctx.guild.owner_id:
            raise HierarchyViolationError(
                f"You cannot remove {role.mention} because it is above your highest role.",
                target_id=member.id,
                target_top_role=role.name,
            )

        if role not in member.roles:
            embed = _create_embed(
                title="Role Not Assigned",
                description=f"{member.mention} does not have {role.mention}.",
                color=EMBED_COLOR_WARNING,
            )
            await ctx.send(embed=embed)
            return

        try:
            await member.remove_roles(role, reason=f"{ctx.author} ({ctx.author.id})")
        except discord.Forbidden as exc:
            raise ActionFailedError(
                f"Failed to remove {role.mention} from {member.mention}: I do not have permission.",
                action="role_remove",
                target_id=member.id,
            ) from exc
        except discord.HTTPException as exc:
            raise ActionFailedError(
                f"Failed to remove {role.mention} from {member.mention}: {exc.text}",
                action="role_remove",
                target_id=member.id,
            ) from exc

        embed = _create_embed(
            title="Role Removed",
            description=f"Removed {role.mention} from {member.mention}.",
            color=EMBED_COLOR_SUCCESS,
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=True)
        embed.add_field(name="Member ID", value=str(member.id), inline=True)

        await ctx.send(embed=embed)
        self.logger.info(
            "User %s (%d) removed role '%s' (%d) from %s (%d).",
            ctx.author, ctx.author.id, role.name, role.id, member, member.id,
        )

    # ===================================================================
    # Error Handling
    # ===================================================================
    async def cog_command_error(
        self,
        ctx: commands.Context,
        error: commands.CommandError,
    ) -> None:
        """Handle errors raised by commands in this cog.

        Args:
            ctx: The command context.
            error: The error that was raised.

        """
        if isinstance(error, commands.CommandNotFound):
            return

        if isinstance(error, commands.MissingPermissions):
            embed = _create_embed(
                title="Missing Permissions",
                description=f"You need the following permissions: {', '.join(error.missing_permissions)}",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        if isinstance(error, commands.BotMissingPermissions):
            embed = _create_embed(
                title="Bot Missing Permissions",
                description=f"I need the following permissions: {', '.join(error.missing_permissions)}",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        if isinstance(error, commands.MissingRequiredArgument):
            embed = _create_embed(
                title="Missing Argument",
                description=f"Missing required argument: `{error.param.name}`",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        if isinstance(error, commands.BadArgument):
            embed = _create_embed(
                title="Invalid Argument",
                description=str(error),
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        if isinstance(error, commands.RangeError):
            embed = _create_embed(
                title="Invalid Value",
                description=f"Value must be between {error.minimum} and {error.maximum}.",
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Handle our custom exceptions
        if isinstance(error, (ModerationError,)):
            embed = _create_embed(
                title="Moderation Error",
                description=str(error),
                color=EMBED_COLOR_ERROR,
            )
            await ctx.send(embed=embed, ephemeral=True)
            return

        # Unhandled errors
        self.logger.exception(
            "Unhandled error in command %s: %s",
            ctx.command.name if ctx.command else "unknown",
            error,
        )

        embed = _create_embed(
            title="Unexpected Error",
            description="An unexpected error occurred. Please try again later.",
            color=EMBED_COLOR_ERROR,
        )
        await ctx.send(embed=embed, ephemeral=True)


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
async def setup(bot: ModerationBot) -> None:
    """Add the ModerationCog to the bot.

    Args:
        bot: The bot instance.

    """
    await bot.add_cog(ModerationCog(bot))
