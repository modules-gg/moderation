"""User model definitions for the moderation module.

This module defines dataclasses representing moderated users and
their moderation-related status within a guild.

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
class UserStatus(Enum):
    """Moderation status of a user within a guild."""

    CLEAN = auto()
    NOTED = auto()
    WARNED = auto()
    TIMED_OUT = auto()
    KICKED = auto()
    BANNED = auto()


# ---------------------------------------------------------------------------
# User Dataclass
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class ModerationUser:
    """A user tracked by the moderation system.

    This represents a user's moderation profile within a specific guild,
    including their case history, warning count, and current status.

    Attributes:
        user_id: The Discord user ID.
        guild_id: The Discord guild ID.
        username: The user's current username.
        display_name: The user's display name in the guild.
        status: The current moderation status.
        case_count: Total number of cases against this user.
        warn_count: Number of active warnings.
        last_case_at: When the most recent case was created.
        created_at: When this record was first created.
        updated_at: When this record was last updated.
        notes: Arbitrary moderator notes about this user.

    """

    user_id: int
    guild_id: int
    username: str = ""
    display_name: str = ""
    status: UserStatus = UserStatus.CLEAN
    case_count: int = 0
    warn_count: int = 0
    last_case_at: datetime | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: list[dict[str, Any]] = field(default_factory=list)

    def increment_case(self) -> None:
        """Increment the case count and update timestamps."""
        self.case_count += 1
        self.last_case_at = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)

    def add_warning(self) -> None:
        """Increment the warning count and update status."""
        self.warn_count += 1
        self.status = UserStatus.WARNED
        self.updated_at = datetime.now(timezone.utc)

    def add_note(self, content: str, moderator_id: int, moderator_name: str) -> None:
        """Add a moderator note to this user's record.

        Args:
            content: The note text.
            moderator_id: The Discord ID of the moderator.
            moderator_name: The name of the moderator.

        """
        self.notes.append({
            "content": content,
            "moderator_id": moderator_id,
            "moderator_name": moderator_name,
            "created_at": datetime.now(timezone.utc).isoformat(),
        })
        if self.status == UserStatus.CLEAN:
            self.status = UserStatus.NOTED
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the user record to a dictionary.

        Returns:
            A dictionary representation of the user record.

        """
        return {
            "user_id": self.user_id,
            "guild_id": self.guild_id,
            "username": self.username,
            "display_name": self.display_name,
            "status": self.status.name,
            "case_count": self.case_count,
            "warn_count": self.warn_count,
            "last_case_at": self.last_case_at.isoformat() if self.last_case_at else None,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "notes": self.notes,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ModerationUser:
        """Deserialize a user record from a dictionary.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A new :class:`ModerationUser` instance.

        """
        return cls(
            user_id=data["user_id"],
            guild_id=data["guild_id"],
            username=data.get("username", ""),
            display_name=data.get("display_name", ""),
            status=UserStatus[data.get("status", "CLEAN")],
            case_count=data.get("case_count", 0),
            warn_count=data.get("warn_count", 0),
            last_case_at=datetime.fromisoformat(data["last_case_at"]) if data.get("last_case_at") else None,
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now(timezone.utc).isoformat())),
            notes=data.get("notes", []),
        )
