"""Moderation log service for the moderation module.

This service handles sending formatted moderation logs to designated
channels logs to designated
channels. It provides consistent embed formatting for all moderation
actions and supports configurable log destinations per guild.

Version 1.1 will integrate with the database layer for persistent
log configuration.

"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

import discord

from moderation.constants import (
    EMBED_COLOR_ERROR,
    EMBED_COLOR_INFO,
    EMBED_COLOR_SUCCESS,
    EMBED_COLOR_WARNING,
)
from moderation.logger import get_logger
from moderation.models.case import Case, CaseAction

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


class ModLogService:
    """Service for sending moderation logs to designated channels.

    Provides methods for logging moderation actions, system events,
    and errors with consistent embed formatting.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        _log_channels: Cache of per-guild log channel IDs.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the ModLogService.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self._log_channels: dict[int, int | None] = {}

    # -------------------------------------------------------------------
    # Configuration
    # -------------------------------------------------------------------
    def set_log_channel(self, guild_id: int, channel_id: int | None) -> None:
        """Set the moderation log channel for a guild.

        Args:
            guild_id: The Discord guild ID.
            channel_id: The channel ID, or None to disable logging.

        """
        self._log_channels[guild_id] = channel_id
        logger.info(
            "Mod log channel for guild %d set to %s",
            guild_id,
            channel_id if channel_id else "disabled",
        )

    def get_log_channel(self, guild_id: int) -> int | None:
        """Get the moderation log channel for a guild.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            The channel ID, or None if not configured.

        """
        return self._log_channels.get(guild_id)

    # -------------------------------------------------------------------
    # Core Logging
    # -------------------------------------------------------------------
    async def log_case(self, case: Case) -> discord.Message | None:
        """Log a moderation case to the guild's mod log channel.

        Args:
            case: The case to log.

        Returns:
            The sent message, or None if logging is disabled or fails.

        """
        channel_id = self.get_log_channel(case.guild_id)
        if channel_id is None:
            return None

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            logger.warning(
                "Mod log channel %d for guild %d is not a text channel",
                channel_id,
                case.guild_id,
            )
            return None

        embed = self._build_case_embed(case)

        try:
            message = await channel.send(embed=embed)
            return message
        except discord.Forbidden:
            logger.warning(
                "Cannot send mod log to channel %d in guild %d: missing permissions",
                channel_id,
                case.guild_id,
            )
        except discord.HTTPException as exc:
            logger.error(
                "Failed to send mod log to channel %d: %s",
                channel_id,
                exc.text,
            )

        return None

    async def log_action(
        self,
        guild_id: int,
        title: str,
        description: str,
        color: int = EMBED_COLOR_INFO,
        fields: list[tuple[str, str, bool]] | None = None,
    ) -> discord.Message | None:
        """Log a generic moderation action.

        Args:
            guild_id: The Discord guild ID.
            title: The embed title.
            description: The embed description.
            color: The embed color.
            fields: Optional list of (name, value, inline) field tuples.

        Returns:
            The sent message, or None if logging is disabled or fails.

        """
        channel_id = self.get_log_channel(guild_id)
        if channel_id is None:
            return None

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return None

        embed = discord.Embed(
            title=title,
            description=description,
            color=color,
            timestamp=datetime.now(timezone.utc),
        )

        if fields:
            for name, value, inline in fields:
                embed.add_field(name=name, value=value, inline=inline)

        try:
            return await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            return None

    async def log_member_join(
        self,
        member: discord.Member,
    ) -> discord.Message | None:
        """Log a member joining the server.

        Args:
            member: The member who joined.

        Returns:
            The sent message, or None if logging is disabled.

        """
        created_at = member.created_at or datetime.now(timezone.utc)
        account_age = datetime.now(timezone.utc) - created_at

        embed = discord.Embed(
            title="Member Joined",
            description=f"{member.mention} ({member.name})",
            color=EMBED_COLOR_SUCCESS,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(
            name="Account Created",
            value=f"{discord.utils.format_dt(created_at, 'R')}\n({created_at.strftime('%Y-%m-%d')})",
            inline=True,
        )
        embed.add_field(
            name="Account Age",
            value=f"{account_age.days} days",
            inline=True,
        )

        return await self._send_embed(member.guild.id, embed)

    async def log_member_remove(
        self,
        member: discord.Member,
    ) -> discord.Message | None:
        """Log a member leaving or being removed from the server.

        Args:
            member: The member who left.

        Returns:
            The sent message, or None if logging is disabled.

        """
        joined_at = member.joined_at or datetime.now(timezone.utc)
        duration = datetime.now(timezone.utc) - joined_at

        embed = discord.Embed(
            title="Member Left",
            description=f"{member.mention} ({member.name})",
            color=EMBED_COLOR_WARNING,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_thumbnail(url=member.display_avatar.url)
        embed.add_field(name="User ID", value=str(member.id), inline=True)
        embed.add_field(
            name="Joined",
            value=f"{discord.utils.format_dt(joined_at, 'R')}",
            inline=True,
        )
        embed.add_field(
            name="Membership Duration",
            value=f"{duration.days} days",
            inline=True,
        )

        return await self._send_embed(member.guild.id, embed)

    async def log_message_delete(
        self,
        message: discord.Message,
    ) -> discord.Message | None:
        """Log a deleted message.

        Args:
            message: The deleted message.

        Returns:
            The sent message, or None if logging is disabled.

        """
        content = message.content or "[no content]"
        if len(content) > 1024:
            content = content[:1021] + "..."

        embed = discord.Embed(
            title="Message Deleted",
            description=f"In {message.channel.mention}",
            color=EMBED_COLOR_ERROR,
            timestamp=datetime.now(timezone.utc),
        )
        embed.set_author(
            name=f"{message.author.name} ({message.author.id})",
            icon_url=message.author.display_avatar.url,
        )
        embed.add_field(name="Content", value=content, inline=False)
        embed.add_field(
            name="Sent",
            value=discord.utils.format_dt(message.created_at, "R"),
            inline=True,
        )

        if message.attachments:
            embed.add_field(
                name="Attachments",
                value=f"{len(message.attachments)} file(s)",
                inline=True,
            )

        return await self._send_embed(message.guild.id, embed)

    # -------------------------------------------------------------------
    # Embed Builders
    # -------------------------------------------------------------------
    def _build_case_embed(self, case: Case) -> discord.Embed:
        """Build a formatted embed for a moderation case.

        Args:
            case: The case to format.

        Returns:
            A :class:`discord.Embed` instance.

        """
        color_map: dict[CaseAction, int] = {
            CaseAction.KICK: EMBED_COLOR_WARNING,
            CaseAction.BAN: EMBED_COLOR_ERROR,
            CaseAction.UNBAN: EMBED_COLOR_SUCCESS,
            CaseAction.TIMEOUT: EMBED_COLOR_WARNING,
            CaseAction.WARN: EMBED_COLOR_WARNING,
            CaseAction.PURGE: EMBED_COLOR_INFO,
            CaseAction.NICKNAME: EMBED_COLOR_INFO,
            CaseAction.LOCK: EMBED_COLOR_WARNING,
            CaseAction.UNLOCK: EMBED_COLOR_SUCCESS,
            CaseAction.ROLE_ADD: EMBED_COLOR_INFO,
            CaseAction.ROLE_REMOVE: EMBED_COLOR_INFO,
            CaseAction.NOTE: EMBED_COLOR_INFO,
        }

        embed = discord.Embed(
            title=f"Case #{case.id} | {case.action.name.replace('_', ' ').title()}",
            description=f"**Target:** {case.target_name} (`{case.target_id}`)\n**Reason:** {case.reason}",
            color=color_map.get(case.action, EMBED_COLOR_INFO),
            timestamp=case.created_at,
        )

        embed.add_field(
            name="Moderator",
            value=f"{case.moderator_name} (`{case.moderator_id}`)",
            inline=True,
        )

        if case.expires_at:
            embed.add_field(
                name="Expires",
                value=discord.utils.format_dt(case.expires_at, "R"),
                inline=True,
            )

        if case.context:
            for key, value in case.context.items():
                embed.add_field(
                    name=key.replace("_", " ").title(),
                    value=str(value),
                    inline=True,
                )

        embed.set_footer(text=f"Status: {case.status.name.replace('_', ' ').title()}")

        return embed

    # -------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------
    async def _send_embed(
        self,
        guild_id: int,
        embed: discord.Embed,
    ) -> discord.Message | None:
        """Send an embed to a guild's mod log channel.

        Args:
            guild_id: The Discord guild ID.
            embed: The embed to send.

        Returns:
            The sent message, or None if sending fails.

        """
        channel_id = self.get_log_channel(guild_id)
        if channel_id is None:
            return None

        channel = self.bot.get_channel(channel_id)
        if not isinstance(channel, discord.TextChannel):
            return None

        try:
            return await channel.send(embed=embed)
        except (discord.Forbidden, discord.HTTPException):
            return None
