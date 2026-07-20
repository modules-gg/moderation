"""Permission and validation checks for the moderation module.

This package contains reusable check functions and predicates used by
commands to validate permissions, hierarchy, and other conditions before
executing moderation actions.

Example:
    Apply a custom check to a command::

        from moderation.checks import is_moderator

        @commands.check(is_moderator)
        async def mycommand(self, ctx):
            ...

"""

from __future__ import annotations

from moderation.checks.permissions import (
    is_bot_owner,
    is_guild_owner,
    is_administrator,
    is_moderator,
    is_helper,
    has_higher_role,
    bot_has_higher_role,
    can_moderate,
)

__all__ = [
    "is_bot_owner",
    "is_guild_owner",
    "is_administrator",
    "is_moderator",
    "is_helper",
    "has_higher_role",
    "bot_has_higher_role",
    "can_moderate",
]
