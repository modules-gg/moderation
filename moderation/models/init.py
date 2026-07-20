"""Data models for the moderation module.

This package defines dataclasses and type definitions representing
moderation entities such as cases, warnings, settings, and audit logs.

Version 1.1 will expand these models with full database integration.
For now, the core data structures are defined for type safety and
future ORM mapping.

"""

from __future__ import annotations

from moderation.models.case import Case, CaseAction, CaseStatus
from moderation.models.user import ModerationUser, UserStatus
from moderation.models.guild import GuildSettings, GuildFeatures

__all__ = [
    "Case",
    "CaseAction",
    "CaseStatus",
    "ModerationUser",
    "UserStatus",
    "GuildSettings",
    "GuildFeatures",
]
