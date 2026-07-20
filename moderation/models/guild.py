"""Guild settings model definitions for the moderation module.

This module defines dataclasses representing per-guild configuration
and feature flags for the moderation system.

Version 1.1 will integrate these models with the database layer.

"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


# ---------------------------------------------------------------------------
# Guild Features
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class GuildFeatures:
    """Feature flags for a guild's moderation configuration.

    Attributes:
        cases_enabled: Whether the case tracking system is active.
        mod_log_enabled: Whether moderation actions are logged to a channel.
        appeal_system_enabled: Whether users can appeal cases.
        automod_enabled: Whether automated moderation is active.
        welcome_messages: Whether to send welcome messages.
        leave_messages: Whether to send leave messages.
        auto_role_enabled: Whether to assign roles on join.
        anti_raid_enabled: Whether anti-raid protection is active.

    """

    cases_enabled: bool = True
    mod_log_enabled: bool = True
    appeal_system_enabled: bool = False
    automod_enabled: bool = False
    welcome_messages: bool = False
    leave_messages: bool = False
    auto_role_enabled: bool = False
    anti_raid_enabled: bool = False


# ---------------------------------------------------------------------------
# Guild Settings
# ---------------------------------------------------------------------------
@dataclass(slots=True)
class GuildSettings:
    """Per-guild moderation settings.

    Attributes:
        guild_id: The Discord guild ID.
        prefix: Custom command prefix for this guild (None = use global).
        mod_log_channel_id: Channel ID for moderation logs.
        appeal_channel_id: Channel ID for appeals.
        mute_role_id: Role ID for muted users.
        auto_role_id: Role ID to assign on join.
        max_warns_before_action: Number of warnings before auto-action.
        warn_action: Action to take on max warns (kick, ban, timeout).
        features: Feature flags for this guild.
        locale: Language/locale code for this guild.
        created_at: When these settings were first created.
        updated_at: When these settings were last updated.

    """

    guild_id: int
    prefix: str | None = None
    mod_log_channel_id: int | None = None
    appeal_channel_id: int | None = None
    mute_role_id: int | None = None
    auto_role_id: int | None = None
    max_warns_before_action: int = 3
    warn_action: str = "timeout"
    features: GuildFeatures = field(default_factory=GuildFeatures)
    locale: str = "en-US"
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def update(self, **kwargs: Any) -> None:
        """Update settings fields and refresh the updated_at timestamp.

        Args:
            **kwargs: Field names and new values to update.

        """
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.updated_at = datetime.now(timezone.utc)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the guild settings to a dictionary.

        Returns:
            A dictionary representation of the settings.

        """
        return {
            "guild_id": self.guild_id,
            "prefix": self.prefix,
            "mod_log_channel_id": self.mod_log_channel_id,
            "appeal_channel_id": self.appeal_channel_id,
            "mute_role_id": self.mute_role_id,
            "auto_role_id": self.auto_role_id,
            "max_warns_before_action": self.max_warns_before_action,
            "warn_action": self.warn_action,
            "features": {
                "cases_enabled": self.features.cases_enabled,
                "mod_log_enabled": self.features.mod_log_enabled,
                "appeal_system_enabled": self.features.appeal_system_enabled,
                "automod_enabled": self.features.automod_enabled,
                "welcome_messages": self.features.welcome_messages,
                "leave_messages": self.features.leave_messages,
                "auto_role_enabled": self.features.auto_role_enabled,
                "anti_raid_enabled": self.features.anti_raid_enabled,
            },
            "locale": self.locale,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> GuildSettings:
        """Deserialize guild settings from a dictionary.

        Args:
            data: The dictionary to deserialize.

        Returns:
            A new :class:`GuildSettings` instance.

        """
        features_data = data.get("features", {})
        features = GuildFeatures(
            cases_enabled=features_data.get("cases_enabled", True),
            mod_log_enabled=features_data.get("mod_log_enabled", True),
            appeal_system_enabled=features_data.get("appeal_system_enabled", False),
            automod_enabled=features_data.get("automod_enabled", False),
            welcome_messages=features_data.get("welcome_messages", False),
            leave_messages=features_data.get("leave_messages", False),
            auto_role_enabled=features_data.get("auto_role_enabled", False),
            anti_raid_enabled=features_data.get("anti_raid_enabled", False),
        )

        return cls(
            guild_id=data["guild_id"],
            prefix=data.get("prefix"),
            mod_log_channel_id=data.get("mod_log_channel_id"),
            appeal_channel_id=data.get("appeal_channel_id"),
            mute_role_id=data.get("mute_role_id"),
            auto_role_id=data.get("auto_role_id"),
            max_warns_before_action=data.get("max_warns_before_action", 3),
            warn_action=data.get("warn_action", "timeout"),
            features=features,
            locale=data.get("locale", "en-US"),
            created_at=datetime.fromisoformat(data.get("created_at", datetime.now(timezone.utc).isoformat())),
            updated_at=datetime.fromisoformat(data.get("updated_at", datetime.now(timezone.utc).isoformat())),
        )
