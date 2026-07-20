"""Localized string catalog for the moderation module.

This module provides a simple string lookup system for bot responses.
Version 1.2 will expand this to load translations from external files
(JSON, PO/MO) and support per-guild/per-user locale preferences.

For now, all strings are defined inline in English with a fallback
mechanism.

"""

from __future__ import annotations

from typing import Any

from moderation.constants import DEFAULT_LOCALE, SUPPORTED_LOCALES

# ---------------------------------------------------------------------------
# String Catalog
# ---------------------------------------------------------------------------
_STRINGS: dict[str, dict[str, str]] = {
    "en-US": {
        # General
        "error.unexpected": "An unexpected error occurred. Please try again later.",
        "error.no_permission": "You do not have permission to use this command.",
        "error.bot_no_permission": "I do not have permission to perform this action.",
        "error.invalid_user": "Could not find that user.",
        "error.invalid_channel": "Could not find that channel.",
        "error.invalid_role": "Could not find that role.",
        "error.invalid_duration": "Invalid duration format. Use formats like `1h30m`, `2d`, or `1w`.",
        "error.hierarchy_violation": "You cannot moderate a user with an equal or higher role.",
        "error.bot_hierarchy": "I cannot moderate that user because their role is above mine.",
        "error.self_moderation": "You cannot perform this action on yourself.",
        "error.owner_immune": "That user is immune to moderation actions.",
        "error.action_failed": "The action failed: {reason}",
        # Commands
        "command.kick.success": "{member} has been kicked.",
        "command.ban.success": "{member} has been banned.",
        "command.unban.success":.success": "{user} has been unbanned.",
        "command.timeout.success": "{member} has been timed out for {duration}.",
        "command.warn.success": "{member} has been warned.",
        "command.purge.success": "Deleted {count} message(s).",
        "command.slowmode.success": "Slowmode set to {seconds} second(s).",
        "command.slowmode.disabled": "Slowmode has been disabled.",
        "command.nickname.success": "Nickname changed to {nickname}.",
        "command.nickname.reset": "Nickname has been reset.",
        "command.lock.success": "{channel} has been locked.",
        "command.unlock.success": "{channel} has been unlocked.",
        "command.roleadd.success": "Added {role} to {member}.",
        "command.roleremove.success": "Removed {role} from {member}.",
        # Confirmations
        "confirm.title": "Confirm Action",
        "confirm.description": "Are you sure you want to {action} {target}?",
        "confirm.yes": "Yes",
        "confirm.no": "No",
        # Logging
        "log.member_join": "Member joined: {member} (ID: {id})",
        "log.member_leave": "Member left: {member} (ID: {id})",
        "log.message_delete": "Message deleted in {channel} by {author}",
        "log.bulk_delete": "Bulk delete in {channel}: {count} messages",
        "log.timeout_applied": "Timeout applied to {member} until {expires}",
        "log.timeout_removed": "Timeout removed from {member}",
        "log.nickname_change": "Nickname changed: {member} — '{before}' → '{after}'",
        "log.role_change": "Roles changed for {member}: +{added} / -{removed}",
        "log.channel_lock": "Channel locked: {channel}",
        "log.channel_unlock": "Channel unlocked: {channel}",
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
def get_string(key: str, locale: str = DEFAULT_LOCALE) -> str:
    """Retrieve a localized string by key.

    Falls back to the default locale if the requested locale or key
    is not found. Falls back to the key itself if the string is missing.

    Args:
        key: The string lookup key.
        locale: The locale code. Defaults to ``en-US``.

    Returns:
        The localized string, or the key if not found.

    Example:
        >>> get_string("command.kick.success")
        '{member} has been kicked.'

    """
    if locale not in SUPPORTED_LOCALES:
        locale = DEFAULT_LOCALE

    catalog = _STRINGS.get(locale, _STRINGS[DEFAULT_LOCALE])
    return catalog.get(key, key)


def get_string_f(key: str, locale: str = DEFAULT_LOCALE, **kwargs: Any) -> str:
    """Retrieve a localized string and format it with keyword arguments.

    Args:
        key: The string lookup key.
        locale: The locale code. Defaults to ``en-US``.
        **kwargs: Keyword arguments to substitute into the string.

    Returns:
        The formatted localized string.

    Example:
        >>> get_string_f("command.kick.success", member="@User")
        '@User has been kicked.'

    """
    template = get_string(key, locale)
    try:
        return template.format(**kwargs)
    except (KeyError, ValueError):
        # If formatting fails, return the unformatted string
        return template


def add_strings(locale: str, strings: dict[str, str]) -> None:
    """Add or override strings for a locale.

    This is useful for plugins or runtime customization.

    Args:
        locale: The locale code.
        strings: A dictionary of key-value string pairs.

    """
    if locale not in _STRINGS:
        _STRINGS[locale] = {}

    _STRINGS[locale].update(strings)
