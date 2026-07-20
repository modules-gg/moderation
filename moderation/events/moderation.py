"""Moderation-related event listeners for the moderation module.

This module implements event handlers that react to Discord gateway events
relevant to moderation: member joins/leaves, message deletions, member
updates (timeouts, nicknames), and guild channel changes.

These events are primarily used for logging and audit purposes. Version 1.1
will expand this to include the case system and mod log integrations.

"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from moderation.constants import EMBED_COLOR_ERROR, EMBED_COLOR_INFO, EMBED_COLOR_WARNING
from moderation.logger import get_logger

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


def _create_log_embed(
    title: str,
    description: str,
    color: int = EMBED_COLOR_INFO,
) -> discord.Embed:
    """Create a standardized embed for event log messages.

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


class ModerationEvents(commands.Cog):
    """Event listeners for moderation-related Discord events.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        logger: A logger for this cog.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the ModerationEvents cog.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self.logger = get_logger(f"{__name__}.ModerationEvents")

    # ===================================================================
    # Member Join
    # ===================================================================
    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member) -> None:
        """Handle member join events.

        Logs when a user joins the server. Future versions may check
        ban lists, alt detection, or welcome messages.

        Args:
            member: The member who joined.

        """
        self.logger.info(
            "Member joined: %s (%d) in guild '%s' (%d). Account created: %s",
            member,
            member.id,
            member.guild.name,
            member.guild.id,
            member.created_at.isoformat(),
        )

        # TODO: v1.1 — Check for existing cases, alt detection, welcome messages

    # ===================================================================
    # Member Remove
    # ===================================================================
    @commands.Cog.listener()
    async def on_member_remove(self, member: discord.Member) -> None:
        """Handle member leave/kick events.

        Logs when a user leaves or is removed from the server. Distinguishing
        between a voluntary leave and a kick requires audit log integration
        (planned for v1.2).

        Args:
            member: The member who left.

        """
        self.logger.info(
            "Member left: %s (%d) from guild '%s' (%d). Joined at: %s",
            member,
            member.id,
            member.guild.name,
            member.guild.id,
            member.joined_at.isoformat() if member.joined_at else "unknown",
        )

    # ===================================================================
    # Message Delete
    # ===================================================================
    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message) -> None:
        """Handle message deletion events.

        Logs deleted messages for moderation purposes. The message cache
        may not contain the content if the bot was restarted recently.

        Args:
            message: The deleted message (from cache).

        """
        if message.author.bot:
            return  # Ignore bot messages

        self.logger.info(
            "Message deleted in #%s (%d) by %s (%d): %r",
            message.channel.name,
            message.channel.id,
            message.author,
            message.author.id,
            message.content[:500] if message.content else "[no content]",
        )

        # TODO: v1.1 — Persist to mod log, handle attachments/embeds

    # ===================================================================
    # Bulk Message Delete
    # ===================================================================
    @commands.Cog.listener()
    async def on_bulk_message_delete(self, messages: list[discord.Message]) -> None:
        """Handle bulk message deletion events (purges).

        Logs when multiple messages are deleted at once, typically from
        the purge command or another bot.

        Args:
            messages: The list of deleted messages (from cache).

        """
        if not messages:
            return

        first = messages[0]
        channel = first.channel

        # Filter out bot messages for count
        user_messages = [m for m in messages if not m.author.bot]

        self.logger.info(
            "Bulk delete in #%s (%d): %d messages (%d from users, %d from bots)",
            channel.name,
            channel.id,
            len(messages),
            len(user_messages),
            len(messages) - len(user_messages),
        )

        # TODO: v1.1 — Persist to mod log with message summaries

    # ===================================================================
    # Member Update (Timeout, Nickname, Roles)
    # ===================================================================
    @commands.Cog.listener()
    async def on_member_update(self, before: discord.Member, after: discord.Member) -> None:
        """Handle member update events.

        Detects timeout changes, nickname changes, and role changes.
        These are logged for moderation tracking.

        Args:
            before: The member before the update.
            after: The member after the update.

        """
        # Timeout change detection
        if before.is_timed_out() != after.is_timed_out():
            if after.is_timed_out():
                self.logger.info(
                    "Member timed out: %s (%d) in '%s' until %s",
                    after,
                    after.id,
                    after.guild.name,
                    after.timed_out_until.isoformat() if after.timed_out_until else "unknown",
                )
            else:
                self.logger.info(
                    "Member timeout expired/removed: %s (%d) in '%s'",
                    after,
                    after.id,
                    after.guild.name,
                )

        # Nickname change detection
        if before.nick != after.nick:
            self.logger.info(
                "Nickname changed: %s (%d) in '%s' — '%s' → '%s'",
                after,
                after.id,
                after.guild.name,
                before.nick,
                after.nick,
            )

        # Role change detection
        before_roles = set(before.roles)
        after_roles = set(after.roles)

        added = after_roles - before_roles
        removed = before_roles - after_roles

        if added:
            role_names = ", ".join(r.name for r in added if r.name != "@everyone")
            if role_names:
                self.logger.info(
                    "Roles added to %s (%d) in '%s': %s",
                    after,
                    after.id,
                    after.guild.name,
                    role_names,
                )

        if removed:
            role_names = ", ".join(r.name for r in removed if r.name != "@everyone")
            if role_names:
                self.logger.info(
                    "Roles removed from %s (%d) in '%s': %s",
                    after,
                    after.id,
                    after.guild.name,
                    role_names,
                )

    # ===================================================================
    # Guild Channel Create
    # ===================================================================
    @commands.Cog.listener()
    async def on_guild_channel_create(self, channel: discord.abc.GuildChannel) -> None:
        """Handle guild channel creation events.

        Logs new channels for moderation tracking.

        Args:
            channel: The newly created channel.

        """
        self.logger.info(
            "Channel created in '%s' (%d): #%s (%d) — type: %s",
            channel.guild.name,
            channel.guild.id,
            channel.name,
            channel.id,
            channel.type.name,
        )

    # ===================================================================
    # Guild Channel Delete
    # ===================================================================
    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel: discord.abc.GuildChannel) -> None:
        """Handle guild channel deletion events.

        Logs deleted channels for moderation tracking.

        Args:
            channel: The deleted channel.

        """
        self.logger.info(
            "Channel deleted in '%s' (%d): #%s (%d) — type: %s",
            channel.guild.name,
            channel.guild.id,
            channel.name,
            channel.id,
            channel.type.name,
        )

    # ===================================================================
    # Guild Channel Update (Lock/Unlock tracking)
    # ===================================================================
    @commands.Cog.listener()
    async def on_guild_channel_update(
        self,
        before: discord.abc.GuildChannel,
        after: discord.abc.GuildChannel,
    ) -> None:
        """Handle guild channel update events.

        Detects permission overwrites changes, particularly lock/unlock
        actions on channels.

        Args:
            before: The channel before the update.
            after: The channel after the update.

        """
        if not isinstance(before, discord.TextChannel) or not isinstance(after, discord.TextChannel):
            return

        # Check @everyone send_messages permission change
        everyone = after.guild.default_role
        before_perms = before.overwrites_for(everyone)
        after_perms = after.overwrites_for(everyone)

        if before_perms.send_messages != after_perms.send_messages:
            if after_perms.send_messages is False:
                self.logger.info(
                    "Channel locked in '%s': #%s (%d)",
                    after.guild.name,
                    after.name,
                    after.id,
                )
            elif after_perms.send_messages is True or after_perms.send_messages is None:
                self.logger.info(
                    "Channel unlocked in '%s': #%s (%d)",
                    after.guild.name,
                    after.name,
                    after.id,
                )

    # ===================================================================
    # Guild Role Create
    # ===================================================================
    @commands.Cog.listener()
    async def on_guild_role_create(self, role: discord.Role) -> None:
        """Handle guild role creation events.

        Args:
            role: The newly created role.

        """
        self.logger.info(
            "Role created in '%s' (%d): @%s (%d) — color: %s, hoist: %s",
            role.guild.name,
            role.guild.id,
            role.name,
            role.id,
            str(role.color),
            role.hoist,
        )

    # ===================================================================
    # Guild Role Delete
    # ===================================================================
    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role) -> None:
        """Handle guild role deletion events.

        Args:
            role: The deleted role.

        """
        self.logger.info(
            "Role deleted in '%s' (%d): @%s (%d)",
            role.guild.name,
            role.guild.id,
            role.name,
            role.id,
        )

    # ===================================================================
    # Guild Ban
    # ===================================================================
    @commands.Cog.listener()
    async def on_member_ban(self, guild: discord.Guild, user: discord.User) -> None:
        """Handle member ban events.

        Logs when a user is banned from a guild.

        Args:
            guild: The guild where the ban occurred.
            user: The banned user.

        """
        self.logger.info(
            "Member banned from '%s' (%d): %s (%d)",
            guild.name,
            guild.id,
            user,
            user.id,
        )

    # ===================================================================
    # Guild Unban
    # ===================================================================
    @commands.Cog.listener()
    async def on_member_unban(self, guild: discord.Guild, user: discord.User) -> None:
        """Handle member unban events.

        Logs when a user is unbanned from a guild.

        Args:
            guild: The guild where the unban occurred.
            user: The unbanned user.

        """
        self.logger.info(
            "Member unbanned from '%s' (%d): %s (%d)",
            guild.name,
            guild.id,
            user,
            user.id,
        )


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
async def setup(bot: ModerationBot) -> None:
    """Add the ModerationEvents cog to the bot.

    Args:
        bot: The bot instance.

    """
    await bot.add_cog(ModerationEvents(bot))
