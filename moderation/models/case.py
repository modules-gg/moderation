"""Case model definitions for the moderation module.

This module defines the :class:`Case` dataclass and related enums
representing moderation actions recorded in the case system.

Version 1.1 will integrate these models with the database layer.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from typing import Any


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class CaseAction(Enum):
    """Types of moderation actions that generate cases."""

    KICK = auto()
    BAN = auto()
    UNBAN = auto()
    TIMEOUT = auto()
    WARN = auto()
    PURGE = auto()
    NICKNAME = auto()
    LOCK = auto()
    UNLOCK = auto()
    SLOWMODE = auto()
    ROLE_ADD = auto()
    ROLE_REMOVE = auto()
    NOTE = auto()


class CaseStatus(Enum):
    """Lifecycle states of a moderation case."""

    ACTIVE = auto()
    APPEALED = auto()
    APPEAL_ACCEPTED = auto()
    APPEAL_DENIED = auto()
    EXPIRED = auto()
    REVERTED = auto()


# ---------------------------------------------------------------------------
# Case Dataclass
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class Case:
    """A recorded moderation action.

    Cases provide an audit trail of moderation decisions, including
    who performed the action, against whom, when, and why. They are
    the foundation of the moderation log system.

    Attributes:
        id: Unique case number (guild-scoped).
        guild_id: The Discord guild ID where the action occurred.
        action: The type of moderation action.
        target_id: The Discord user ID of the moderated user.
        target_name: The display name of the target at the time.
        moderator_id: The Discord user ID of the acting moderator.
        moderator_name: The display name of the moderator at the time.
        reason: The stated reason for the action.
        created_at: When the case was created.
        expires_at: When the action expires (for timeouts, bans, etc.).
        status: The current case status.
        context: Additional action-specific data (duration, message count, etc.).
        appeal_id: Reference to an associated appeal, if any.

    """

    id: int
    guild_id: int
    action: CaseAction
    target_id: int
    target_name: str
    moderator_id: int
    moderator_name: str
    reason: str = "No reason provided."
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime | None = None
    status: CaseStatus = CaseStatus.ACTIVE
    context: dict[str, Any] = field(default_factory=dict)
    appeal_id: int | None = None

    @property
    def is_expired(self) -> bool:
        """Check if the case action has expired.

        Returns:
            True if the case has an expiration time that has passed.

        """
        if self.expires_at is None:
            return False
        return datetime.now(timezone.utc) >= self.expires_at

    @property
    def duration_seconds(self) -> int | None:
        """Calculate the action duration in seconds.

        Returns:
            The duration if expires_at is set, None otherwise.

        """
        if self.expires_at is None:
            return None
        delta = self.expires_at - self.created_at
        return int(delta.total_seconds())

    def to_dict(self) -> dict[str, Any]:
        """Serialize the case to a dictionary.

        Returns:
            A dictionary representation of the case.

        """
        return {
            "id": self.id,
            "guild_id": self.guild_id,
            "action": self.action.name,
            "target_id": self.target_id,
            "target_name": self.target_name,
            "moderator_id": self.moderator_id,
            "moderator_name": self.moderator_name,
            "reason": self.reason,
            "created_at": self.created_at.isoformat(),
            "expires_at": self.expires_at.isoformat() if self.expires_at else None,
            "status": self.status.name,
            "context": self.context,
            "appeal_id": self.appeal_id,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Case:
        """Deserialize a case from a dictionary.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A new :class:`Case` instance.

        """
        return cls(
            id=data["id"],
            guild_id=data["guild_id"],
            action=CaseAction[data["action"]],
            target_id=data["target_id"],
            target_name=data["target_name"],
            moderator_id=data["moderator_id"],
            moderator_name=data["moderator_name"],
            reason=data.get("reason", "No reason provided."),
            created_at=datetime.fromisoformat(data["created_at"]),
            expires_at=datetime.fromisoformat(data["expires_at"]) if data.get("expires_at") else None,
            status=CaseStatus[data.get("status", "ACTIVE")],
            context=data.get("context", {}),
            appeal_id=data.get("appeal_id"),
        )
