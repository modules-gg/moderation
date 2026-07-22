"""Case management service for the moderation module.

This service encapsulates all business logic related to moderation
cases: creation, retrieval, updates, appeals, and expiration handling.

Version 1.1 will integrate this service with the database layer.
For now, it operates as an in-memory registry with async-ready methods.

"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import TYPE_CHECKING, Any

from moderation.constants import CaseType
from moderation.exceptions.commands import CaseNotFoundError
from moderation.logger import get_logger
from moderation.models.case import Case, CaseAction, CaseStatus

if TYPE_CHECKING:
    from moderation.bot import ModerationBot

logger = get_logger(__name__)


class CaseService:
    """Service for managing moderation cases.

    Provides methods for creating, retrieving, updating, and closing
    moderation cases. Acts as the single source of truth for case
    operations across the bot.

    Attributes:
        bot: The :class:`ModerationBot` instance.
        _cases: In-memory case registry, keyed by (guild_id, case_id).
        _case_counters: Per-guild case number counters.

    """

    def __init__(self, bot: ModerationBot) -> None:
        """Initialize the CaseService.

        Args:
            bot: The bot instance.

        """
        self.bot: ModerationBot = bot
        self._cases: dict[tuple[int, int], Case] = {}
        self._case_counters: dict[int, int] = {}

    # -------------------------------------------------------------------
    # Case Creation
    # -------------------------------------------------------------------
    async def create_case(
        self,
        guild_id: int,
        action: CaseAction,
        target_id: int,
        target_name: str,
        moderator_id: int,
        moderator_name: str,
        reason: str = "No reason provided.",
        expires_at: datetime | None = None,
        context: dict[str, Any] | None = None,
    ) -> Case:
        """Create a new moderation case.

        Args:
            guild_id: The Discord guild ID.
            action: The type of moderation action.
            target_id: The Discord user ID of the target.
            target_name: The display name of the target.
            moderator_id: The Discord user ID of the moderator.
            moderator_name: The display name of the moderator.
            reason: The reason for the action.
            expires_at: When the action expires, if applicable.
            context: Additional action-specific data.

        Returns:
            The newly created :class:`Case` instance.

        """
        case_id = self._next_case_id(guild_id)

        case = Case(
            id=case_id,
            guild_id=guild_id,
            action=action,
            target_id=target_id,
            target_name=target_name,
            moderator_id=moderator_id,
            moderator_name=moderator_name,
            reason=reason,
            expires_at=expires_at,
            context=context or {},
        )

        self._cases[(guild_id, case_id)] = case

        logger.info(
            "Case #%d created in guild %d: %s against %s (%d) by %s (%d)",
            case_id,
            guild_id,
            action.name,
            target_name,
            target_id,
            moderator_name,
            moderator_id,
        )

        # TODO: v1.1 — Persist to database, emit mod log event

        return case

    # -------------------------------------------------------------------
    # Case Retrieval
    # -------------------------------------------------------------------
    async def get_case(self, guild_id: int, case_id: int) -> Case:
        """Retrieve a case by guild and case number.

        Args:
            guild_id: The Discord guild ID.
            case_id: The case number.

        Returns:
            The :class:`Case` instance.

        Raises:
            CaseNotFoundError: If the case does not exist.

        """
        case = self._cases.get((guild_id, case_id))
        if case is None:
            raise CaseNotFoundError(
                f"Case #{case_id} not found in this server.",
                case_id=case_id,
            )
        return case

    async def get_cases_by_user(
        self,
        guild_id: int,
        user_id: int,
        action: CaseAction | None = None,
    ) -> list[Case]:
        """Retrieve all cases for a specific user.

        Args:
            guild_id: The Discord guild ID.
            user_id: The Discord user ID.
            action: Optional filter by action type.

        Returns:
            A list of matching :class:`Case` instances.

        """
        cases = [
            case
            for case in self._cases.values()
            if case.guild_id == guild_id and case.target_id == user_id
        ]

        if action is not None:
            cases = [c for c in cases if c.action == action]

        return sorted(cases, key=lambda c: c.created_at, reverse=True)

    async def get_cases_by_moderator(
        self,
        guild_id: int,
        moderator_id: int,
    ) -> list[Case]:
        """Retrieve all cases created by a specific moderator.

        Args:
            guild_id: The Discord guild ID.
            moderator_id: The Discord user ID of the moderator.

        Returns:
            A list of matching :class:`Case` instances.

        """
        cases = [
            case
            for case in self._cases.values()
            if case.guild_id == guild_id and case.moderator_id == moderator_id
        ]
        return sorted(cases, key=lambda c: c.created_at, reverse=True)

    async def get_recent_cases(
        self,
        guild_id: int,
        limit: int = 10,
    ) -> list[Case]:
        """Retrieve the most recent cases in a guild.

        Args:
            guild_id: The Discord guild ID.
            limit: Maximum number of cases to return. Defaults to 10.

        Returns:
            A list of :class:`Case` instances.

        """
        cases = [
            case
            for case in self._cases.values()
            if case.guild_id == guild_id
        ]
        return sorted(cases, key=lambda c: c.created_at, reverse=True)[:limit]

    # -------------------------------------------------------------------
    # Case Updates
    # -------------------------------------------------------------------
    async def update_reason(
        self,
        guild_id: int,
        case_id: int,
        new_reason: str,
        updated_by: int,
    ) -> Case:
        """Update the reason for an existing case.

        Args:
            guild_id: The Discord guild ID.
            case_id: The case number.
            new_reason: The new reason text.
            updated_by: The Discord user ID making the update.

        Returns:
            The updated :class:`Case` instance.

        Raises:
            CaseNotFoundError: If the case does not exist.

        """
        case = await self.get_case(guild_id, case_id)
        old_reason = case.reason
        case.reason = new_reason

        logger.info(
            "Case #%d reason updated by %d: '%s' -> '%s'",
            case_id,
            updated_by,
            old_reason,
            new_reason,
        )

        # TODO: v1.1 — Persist update to database

        return case

    async def close_case(
        self,
        guild_id: int,
        case_id: int,
        status: CaseStatus = CaseStatus.EXPIRED,
    ) -> Case:
        """Close a case with a specific status.

        Args:
            guild_id: The Discord guild ID.
            case_id: The case number.
            status: The closing status. Defaults to EXPIRED.

        Returns:
            The updated :class:`Case` instance.

        Raises:
            CaseNotFoundError: If the case does not exist.

        """
        case = await self.get_case(guild_id, case_id)
        case.status = status

        logger.info(
            "Case #%d closed with status %s",
            case_id,
            status.name,
        )

        # TODO: v1.1 — Persist update to database

        return case

    async def appeal_case(
        self,
        guild_id: int,
        case_id: int,
        appeal_id: int,
    ) -> Case:
        """Mark a case as appealed.

        Args:
            guild_id: The Discord guild ID.
            case_id: The case number.
            appeal_id: The ID of the associated appeal.

        Returns:
            The updated :class:`Case` instance.

        Raises:
            CaseNotFoundError: If the case does not exist.

        """
        case = await self.get_case(guild_id, case_id)
        case.status = CaseStatus.APPEALED
        case.appeal_id = appeal_id

        logger.info(
            "Case #%d marked as appealed (appeal #%d)",
            case_id,
            appeal_id,
        )

        # TODO: v1.1 — Persist update to database

        return case

    # -------------------------------------------------------------------
    # Expiration
    # -------------------------------------------------------------------
    async def get_expired_cases(self, guild_id: int | None = None) -> list[Case]:
        """Retrieve all cases that have expired.

        Args:
            guild_id: Optional guild filter. If None, checks all guilds.

        Returns:
            A list of expired :class:`Case` instances.

        """
        now = datetime.now(timezone.utc)
        cases = self._cases.values()

        if guild_id is not None:
            cases = [c for c in cases if c.guild_id == guild_id]

        return [c for c in cases if c.is_expired and c.status == CaseStatus.ACTIVE]

    # -------------------------------------------------------------------
    # Internal
    # -------------------------------------------------------------------
    def _next_case_id(self, guild_id: int) -> int:
        """Generate the next case number for a guild.

        Args:
            guild_id: The Discord guild ID.

        Returns:
            The next sequential case number.

        """
        current = self._case_counters.get(guild_id, 0)
        next_id = current + 1
        self._case_counters[guild_id] = next_id
        return next_id
