"""User management service for the moderation module.

This service encapsulates business logic for tracking moderated users,
managing warnings, notes, and user status within guilds.

Version 1.1 will integrate this service with the database layer.
For now, it operates as an in-memory registry with async-ready methods.

"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from moderation.exceptions.database import RecordNotFoundError
from moderation.logger import get_logger
from moderation.models.user import ModerationUser, UserStatus

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


class UserService:
    """Service for managing moderated user records.

    Provides methods for tracking user moderation history, warnings,
    notes, and status updates across guilds.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        _users: In-memory user registry, keyed by (guild_id, user_id).

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the UserService.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self._users: dict[tuple[int, int], ModerationUser] = {}

    # -------------------------------------------------------------------
    # User Retrieval / Creation
    # -------------------------------------------------------------------
    async def get_or_create_user(
        self,
        guild_id: int,
        user_id: int,
        username: str = "",
        display_name: str = "",
    ) -> ModerationUser:
        """Retrieve an existing user record or create a new one.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            username: The user's current username.
            display_name: The user's display name in the guild.

        Returns:
            The :class:`ModerationUser` instance.

        """
        key = (guild_id, user_id)
        user = self._users.get(key)

        if user is None:
            user = ModerationUser(
                user_id=user_id,
                guild_id=guild_id,
                username=username,
                display_name=display_name,
            )
            self._users[key] = user
            logger.debug(
                "Created moderation record for user %d in guild %d",
                user_id,
                guild_id,
            )

        # Update names if they changed
        if username and user.username != username:
            user.username = username
        if display_name and user.display_name != display_name:
            user.display_name = display_name

        return user

    async def get_user(self, guild_id: int, user_id: int) -> ModerationUser:
        """Retrieve an existing user record.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.

        Returns:
            The :class:`ModerationUser` instance.

        Raises:
            RecordNotFoundError: If the user record does not exist.

        """
        key = (guild_id, user_id)
        user = self._users.get(key)
        if user is None:
            raise RecordNotFoundError(
                f"No moderation record found for user {user_id} in guild {guild_id}.",
                table="moderation_users",
                query_params={"guild_id": guild_id, "user_id": user_id},
            )
        return user

    async def get_users_by_status(
        self,
        guild_id: int,
        status: UserStatus,
    ) -> list[ModerationUser]:
        """Retrieve all users with a specific moderation status.

        Args:
            guild_id: The Discord guild ID.
            status: The status to filter by.

        Returns:
            A list of :class:`ModerationUser` instances.

        """
        users = [
            user
            for user in self._users.values()
            if user.guild_id == guild_id and user.status == status
        ]
        return sorted(users, key=lambda u: u.updated_at, reverse=True)

    # -------------------------------------------------------------------
    # Warnings
    # -------------------------------------------------------------------
    async def add_warning(
        self,
        guild_id: int,
        user_id: int,
        reason: str,
        moderator_id: int,
        moderator_name: str,
    ) -> ModerationUser:
        """Add a warning to a user's record.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            reason: The warning reason.
            moderator_id: The moderator's Discord ID.
            moderator_name: The moderator's name.

        Returns:
            The updated :class:`ModerationUser` instance.

        """
        user = await self.get_or_create_user(guild_id, user_id)
        user.add_warning()

        # Add warning as a note for paper trail
        user.add_note(
            content=f"Warning: {reason}",
            moderator_id=moderator_id,
            moderator_name=moderator_name,
        )

        logger.info(
            "Warning added to user %d in guild %d by %s (%d). Reason: %s",
            user_id,
            guild_id,
            moderator_name,
            moderator_id,
            reason,
        )

        # TODO: v1.1 — Check max_warns threshold, auto-action

        return user

    async def clear_warnings(
        self,
        guild_id: int,
        user_id: int,
        cleared_by: int,
    ) -> ModerationUser:
        """Clear all warnings from a user's record.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            cleared_by: The Discord ID of the moderator clearing warnings.

        Returns:
            The updated :class:`ModerationUser` instance.

        Raises:
            RecordNotFoundError: If the user record does not exist.

        """
        user = await self.get_user(guild_id, user_id)
        old_count = user.warn_count
        user.warn_count = 0

        if user.status == UserStatus.WARNED:
            user.status = UserStatus.CLEAN

        user.updated_at = datetime.now(timezone.utc)

        logger.info(
            "Cleared %d warning(s) for user %d in guild %d (cleared by %d)",
            old_count,
            user_id,
            guild_id,
            cleared_by,
        )

        return user

    # -------------------------------------------------------------------
    # Notes
    # -------------------------------------------------------------------
    async def add_note(
        self,
        guild_id: int,
        user_id: int,
        content: str,
        moderator_id: int,
        moderator_name: str,
    ) -> ModerationUser:
        """Add a moderator note to a user's record.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            content: The note text.
            moderator_id: The moderator's Discord ID.
            moderator_name: The moderator's name.

        Returns:
            The updated :class:`ModerationUser` instance.

        """
        user = await self.get_or_create_user(guild_id, user_id)
        user.add_note(
            content=content,
            moderator_id=moderator_id,
            moderator_name=moderator_name,
        )

        logger.info(
            "Note added to user %d in guild %d by %s (%d)",
            user_id,
            guild_id,
            moderator_name,
            moderator_id,
        )

        return user

    # -------------------------------------------------------------------
    # Status Management
    # -------------------------------------------------------------------
    async def update_status(
        self,
        guild_id: int,
        user_id: int,
        status: UserStatus,
    ) -> ModerationUser:
        """Update a user's moderation status.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            status: The new status.

        Returns:
            The updated :class:`ModerationUser` instance.

        """
        user = await self.get_or_create_user(guild_id, user_id)
        old_status = user.status
        user.status = status
        user.updated_at = datetime.now(timezone.utc)

        logger.info(
            "User %d status in guild %d changed from %s to %s",
            user_id,
            guild_id,
            old_status.name,
            status.name,
        )

        return user

    # -------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------
    async def get_guild_stats(self, guild_id: int) -> dict[str, Any]:
        """Get moderation statistics for a guild.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            A dictionary of statistics.

        """
        users = [u for u in self._users.values() if u.guild_id == guild_id]

        return {
            "total_tracked": len(users),
            "clean": len([u for u in users if u.status == UserStatus.CLEAN]),
            "noted": len([u for u in users if u.status == UserStatus.NOTED]),
            "warned": len([u for u in users if u.status == UserStatus.WARNED]),
            "timed_out": len([u for u in users if u.status == UserStatus.TIMED_OUT]),
            "kicked": len([u for u in users if u.status == UserStatus.KICKED]),
            "banned": len([u for u in users if u.status == UserStatus.BANNED]),
            "total_warnings": sum(u.warn_count for u in users),
            "total_notes": sum(len(u.notes) for u in users),
        }
