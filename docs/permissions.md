# Permissions Guide

This document explains the permission system and role hierarchy used by the modules.gg Moderation Bot.

---

## Discord Permissions

The bot uses Discord's native permission system. Each command requires specific permissions from both the invoking user and the bot itself.

---

### Command Permission Requirements

| Command | User Permission | Bot Permission |
|---------|---------------|----------------|
| `kick` | Kick Members | Kick Members |
| `ban` | Ban Members | Ban Members |
| `timeout` | Moderate Members | Moderate Members |
| `warn` | Manage Messages | Manage Messages |
| `unban` | Ban Members | Ban Members |
| `purge` | Manage Messages | Manage Messages, Read Message History |
| `slowmode` | Manage Channels | Manage Channels Channels | Manage Channels |
| `nickname` | Manage Nicknames | Manage Nicknames |
| `lock` | Manage Channels | Manage Channels |
| `unlock` | Manage Channels | Manage Channels |
| `roleadd` | Manage Roles | Manage Roles |
| `roleremove` | Manage Roles | Manage Roles |

---

## Role Hierarchy

Discord enforces a strict role hierarchy. The bot implements additional checks beyond Discord's native permissions.

### Hierarchy Rules

1. **Server Owner** is immune to all moderation actions
2. **Bot Owners** are immune to most actions (configurable via `owner_ids`)
3. **Higher Roles** cannot be moderated by users with lower or equal roles
4. **Bot's Top Role** must be above the target's top role

### Visual Example

```

Server Owner (highest)
├── Admin Role
│   └── Moderator Role
│       └── Helper Role
│           └── @everyone (lowest)
└── Bot Role (must be above targets)

```

### Scenarios

| Scenario | Result |
|----------|--------|
| Moderator tries to kick Admin | ❌ Blocked — hierarchy violation |
| Helper tries to timeout Moderator | ❌ Blocked — hierarchy violation |
| Bot tries to ban Admin | ❌ Blocked — bot hierarchy too low |
| Admin tries to kick Moderator | ✅ Allowed — higher role |
| Moderator tries to kick Helper | ✅ Allowed — higher role |
| User tries to kick themselves | ❌ Blocked — self-moderation |

---

## Permission Checks Flow

When a moderation command is invoked, the following checks run in order:

```

1. Command invoked
   ↓
2. Discord permission check (user has required permission?)
   ↓ NO → "Missing Permissions" error
   ↓
3. Bot permission check (bot has required permission?)
   ↓ NO → "Bot Missing Permissions" error
   ↓
4. Self-moderation check (target is not the invoker)
   ↓ NO → "Self Moderation" error
   ↓
5. Owner immunity check (target is not server/bot owner)
   ↓ NO → "Owner Immune" error
   ↓
6. Hierarchy check (invoker's top role > target's top role)
   ↓ NO → "Hierarchy Violation" error
   ↓
7. Bot hierarchy check (bot's top role > target's top role)
   ↓ NO → "Bot Hierarchy" error
   ↓
8. Action executed

```

---

## Setting Up Roles for Moderation

### Recommended Role Structure

| Role | Permissions | Purpose |
|------|-------------|---------|
| Bot Role | Administrator (or all moderation perms) | Bot operations |
| Server Owner | All | Server ownership |
| Admin | Administrator | Full server management |
| Senior Mod | Ban Members, Manage Channels, Manage Roles | Advanced moderation |
| Moderator | Kick Members, Moderate Members, Manage Messages | Standard moderation |
| Helper | Manage Messages | Basic moderation, warnings |
| @everyone | None | Regular members |

### Bot Role Position

The bot's role **must** be positioned above all roles it needs to moderate. In Discord:

1. Open Server Settings → Roles
2. Drag the bot's role above Moderator, Helper, etc.
3. Keep it below Admin/Owner unless you want the bot to manage admins

---

## Custom Permission Checks

You can implement custom checks using the `moderation.checks` module:

```python
from moderation.checks import is_moderator, can_moderate

@commands.check(is_moderator)
async def mycommand(self, ctx):
    ...

# Or use the composite check
@commands.check(can_moderate(target=some_member))
async def ban_user(self, ctx, member: discord.Member):
    ...
```

---

Troubleshooting

Issue	Cause	Solution	
"Missing Permissions"	User lacks required Discord permission	Grant the permission in Server Settings → Roles	
"Bot Missing Permissions"	Bot lacks required permission	Check bot's role permissions or re-invite with correct scopes	
"Hierarchy Violation"	Target has equal/higher role	Move your role above the target's, or have an admin perform the action	
"Bot Hierarchy"	Bot's role is below target's	Move the bot's role above the target's role in Server Settings	
"Owner Immune"	Target is server owner	Server owners cannot be moderated by anyone	
"Self Moderation"	You targeted yourself	You cannot moderate yourself	

---

Audit Log

All moderation actions are logged with the moderator's name and ID in the reason field. You can view these in:

- Discord's native Audit Log (Server Settings → Audit Log)
- The bot's mod log channel (when configured in v1.1)

---

Need help? Open a [GitHub Discussion](https://github.com/modules-gg/moderation/discussions).
