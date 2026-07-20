"""Permission check predicates for moderation commands.

This module defines reusable check functions that validate whether a user
or the bot has sufficient permissions and hierarchy to perform moderation
actions. These checks are designed to be used with discord.py's
``@commands.check()`` decorator or called directly in command logic.

All checks raise :class:`commands.CheckFailure` or a subclass when the
condition is not met, allowing for consistent error handling.

"""

from __future__ import annotations

from typing import TYPE_CHECKING

import discord
from discord.ext import commands

from moderation.exceptions.checks import (
    BotHierarchyError,
    HierarchyViolationError,
    InsufficientPermissionsError,
    OwnerImmuneError,
    SelfModerationError,
)

if TYPE_CHECKING:
    from moderation.bot import ModerationBot


# ---------------------------------------------------------------------------
# Role/Permission Level Checks
# ---------------------------------------------------------------------------
def is_bot_owner() -> commands.Check:
    """Check if the invoking user is a bot owner.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        bot: ModerationBot = ctx.bot
        owner_ids: list[int] = bot.config.get("bot", {}).get("owner_ids", [])
        if ctx.author.id not in owner_ids:
            raise commands.NotOwner("You must be a bot owner to use this command.")
        return True

    return commands.check(predicate)


def is_guild_owner() -> commands.Check:
    """Check if the invoking user is the guild owner.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.id != ctx.guild.owner_id:
            raise InsufficientPermissionsError(
                "You must be the server owner to use this command.",
                required_permission="guild_owner",
                user_id=ctx.author.id,
            )
        return True

    return commands.check(predicate)


def is_administrator() -> commands.Check:
    """Check if the invoking user has administrator permissions.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.author.guild_permissions.administrator:
            raise InsufficientPermissionsError(
                "You must have Administrator permission to use this command.",
                required_permission="administrator",
                user_id=ctx.author.id,
            )
        return True

    return commands.check(predicate)


def is_moderator() -> commands.Check:
    """Check if the invoking user has moderation permissions.

    This checks for kick_members, ban_members, or manage_messages.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        perms = ctx.author.guild_permissions
        if not any(
            (
                perms.kick_members,
                perms.ban_members,
                perms.manage_messages,
                perms.moderate_members,
            )
        ):
            raise InsufficientPermissionsError(
                "You must have moderation permissions to use this command.",
                required_permission="moderator",
                user_id=ctx.author.id,
            )
        return True

    return commands.check(predicate)


def is_helper() -> commands.Check:
    """Check if the invoking user has helper-level permissions.

    This checks for manage_messages as a baseline helper permission.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.author.guild_permissions.manage_messages:
            raise InsufficientPermissionsError(
                "You must have Manage Messages permission to use this command.",
                required_permission="manage_messages",
                user_id=ctx.author.id,
            )
        return True

    return commands.check(predicate)


# ---------------------------------------------------------------------------
# Hierarchy Checks
# ---------------------------------------------------------------------------
def has_higher_role(target: discord.Member) -> commands.Check:
    """Check if the invoking user has a higher role than the target.

    Args:
        target: The member to compare against.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.author.id == ctx.guild.owner_id:
            return True

        if ctx.author.top_role.position <= target.top_role.position:
            raise HierarchyViolationError(
                f"You cannot moderate {target.mention} because they have an equal or higher role.",
                target_id=target.id,
                target_top_role=target.top_role.name,
            )
        return True

    return commands.check(predicate)


def bot_has_higher_role(target: discord.Member) -> commands.Check:
    """Check if the bot has a higher role than the target.

    Args:
        target: The member to compare against.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        bot_member = ctx.guild.me
        if bot_member.top_role.position <= target.top_role.position:
            raise BotHierarchyError(
                f"I cannot moderate {target.mention} because their highest role is above mine.",
                bot_top_role=bot_member.top_role.name,
                target_top_role=target.top_role.name,
            )
        return True

    return commands.check(predicate)


# ---------------------------------------------------------------------------
# Composite Checks
# ---------------------------------------------------------------------------
def can_moderate(target: discord.Member) -> commands.Check:
    """Composite check for full moderation validation.

    Validates:
    1. Target is not the invoking user.
    2. Target is not the guild owner.
    3. Invoker has higher role than target (or is guild owner).
    4. Bot has higher role than target.

    Args:
        target: The member to be moderated.

    Returns:
        A :class:`commands.Check` predicate.

    """
    async def predicate(ctx: commands.Context) -> bool:
        # Self-moderation check
        if target.id == ctx.author.id:
            raise SelfModerationError(action=ctx.command.name if ctx.command else "unknown")

        # Guild owner immunity
        if target.id == ctx.guild.owner_id:
            raise OwnerImmuneError(
                "You cannot moderate the server owner.",
                target_id=target.id,
                reason="guild_owner",
            )

        # Hierarchy checks
        if ctx.author.id != ctx.guild.owner_id:
            if ctx.author.top_role.position <= target.top_role.position:
                raise HierarchyViolationError(
                    f"You cannot moderate {target.mention} because they have an equal or higher role.",
                    target_id=target.id,
                    target_top_role=target.top_role.name,
                )

        bot_member = ctx.guild.me
        if bot_member.top_role.position <= target.top_role.position:
            raise BotHierarchyError(
                f"I cannot moderate {target.mention} because their highest role is above mine.",
                bot_top_role=bot_member.top_role.name,
                target_top_role=target.top_role.name,
            )

        return True

    return commands.check(predicate)


# ---------------------------------------------------------------------------
# Direct Call Helpers (for use in command body)
# ---------------------------------------------------------------------------
async def check_hierarchy(
    ctx: commands.Context,
    target: discord.Member,
) -> None:
    """Directly validate hierarchy without using a decorator.

    This is useful when the target is determined at runtime (e.g., from
    a command argument) rather than at decoration time.

    Args:
        ctx: The command context.
        target: The member to validate against.

    Raises:
        SelfModerationError: If target is the invoking user.
        OwnerImmuneError: If target is the guild owner.
        HierarchyViolationError: If invoker cannot action target.
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

    if ctx.author.id != ctx.guild.owner_id:
        if ctx.author.top_role.position <= target.top_role.position:
            raise HierarchyViolationError(
                f"You cannot moderate {target.mention} because they have an equal or higher role.",
                target_id=target.id,
                target_top_role=target.top_role.name,
            )

    bot_member = ctx.guild.me
    if bot_member.top_role.position <= target.top_role.position:
        raise BotHierarchyError(
            f"I cannot moderate {target.mention} because their highest role is above mine.",
            bot_top_role=bot_member.top_role.name,
            target_top_role=target.top_role.name,
        )


async def check_bot_hierarchy(
    guild: discord.Guild,
    target: discord.Member | discord.Role,
) -> None:
    """Check if the bot can action a target member or role.

    Args:
        guild: The guild context.
        target: The member or role to validate.

    Raises:
        BotHierarchyError: If bot cannot action the target.

    """
    bot_member = guild.me

    if isinstance(target, discord.Member):
        if bot_member.top_role.position <= target.top_role.position:
            raise BotHierarchyError(
                f"I cannot moderate {target.mention} because their highest role is above mine.",
                bot_top_role=bot_member.top_role.name,
                target_top_role=target.top_role.name,
            )
    elif isinstance(target, discord.Role):
        if bot_member.top_role.position <= target.position:
            raise BotHierarchyError(
                f"I cannot manage {target.mention} because it is above my highest role.",
                bot_top_role=bot_member.top_role.name,
                target_top_role=target.name,
            )
