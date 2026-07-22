# Commands Reference

This document lists all available commands in the modules.gg Moderation Module.

---

## Command Prefix

By default, commands use the prefix `!` or can be invoked by mentioning the bot. Slash commands are also available for all moderation commands.

---

## Core Moderation Commands

### `kick`
Kick a member from the server.

**Usage:** `!kick <member> [reason]`

**Permissions:** Kick Members

**Arguments:**
- `member` — The member to kick (mention or ID)
- `reason` — Optional reason for the kick

**Example:**
```

!kick @Spammer Repeated spam in general

```

---

### `ban`
Ban a member from the server.

**Usage:** `!ban <member> [delete_days] [reason]`

**Permissions:** Ban Members

**Arguments:**
- `member` — The member to ban (mention or ID)
- `delete_days` — Days of message history to delete (0-7). Default: 1
- `reason` — Optional reason for the ban

**Example:**
```

!ban @ToxicUser 7 Harassment and threats

```

---

### `timeout`
Timeout a member for a specified duration.

**Usage:** `!timeout <member> <duration> [reason]`

**Permissions:** Moderate Members

**Arguments:**
- `member` — The member to timeout (mention or ID)
- `duration` — Duration string (e.g., `1h`, `30m`, `1d`, `1w`)
- `reason` — Optional reason for the timeout

**Duration Formats:**
| Format | Meaning |
|--------|---------|
| `30s` | 30 seconds |
| `5m` | 5 minutes |
| `1h30m` | 1 hour 30 minutes |
| `2d` | 2 days |
| `1w` | 1 week |

**Example:**
```

!timeout @DisruptiveUser 2d Repeated off-topic arguments

```

---

### `warn`
Issue a warning to a member.

**Usage:** `!warn <member> [reason]`

**Permissions:** Manage Messages

**Arguments:**
- `member` — The member to warn (mention or ID)
- `reason` — Optional reason for the warning

**Example:**
```

!warn @RuleBreaker Minor rule violation

```

---

### `unban`
Unban a user from the server.

**Usage:** `!unban <user> [reason]`

**Permissions:** Ban Members

**Arguments:**
- `user` — The user to unban (ID or mention)
- `reason` — Optional reason for the unban

**Example:**
```

!unban 123456789012345678 User appealed and was forgiven

```

---

### `purge`
Delete messages from the current channel.

**Usage:** `!purge <amount> [user]`

**Permissions:** Manage Messages

**Arguments:**
- `amount` — Number of messages to delete (1-1000)
- `user` — Optional: only delete messages from this user

**Example:**
```

!purge 50
!purge 100 @Spammer

```

---

### `slowmode`
Set or disable slowmode for the current channel.

**Usage:** `!slowmode <seconds>`

**Permissions:** Manage Channels

**Arguments:**
- `seconds` — Slowmode delay in seconds (0 to disable, max 21600)

**Example:**
```

!slowmode 5
!slowmode 0

```

---

### `nickname`
Change or reset a member's nickname.

**Usage:** `!nickname <member> [nickname]`

**Permissions:** Manage Nicknames

**Arguments:**
- `member` — The member whose nickname to change
- `nickname` — The new nickname. Omit to reset.

**Example:**
```

!nickname @User New Nickname
!nickname @User

```

---

### `lock`
Lock a channel so @everyone cannot send messages.

**Usage:** `!lock [channel] [reason]`

**Permissions:** Manage Channels

**Arguments:**
- `channel` — The channel to lock (defaults to current)
- `reason` — Optional reason

**Example:**
```

!lock
!lock #general Raid prevention

```

---

### `unlock`
Unlock a channel so @everyone can send messages.

**Usage:** `!unlock [channel] [reason]`

**Permissions:** Manage Channels

**Arguments:**
- `channel` — The channel to unlock (defaults to current)
- `reason` — Optional reason

**Example:**
```

!unlock
!unlock #general Raid over

```

---

### `roleadd`
Add a role to a member.

**Usage:** `!roleadd <member> <role>`

**Permissions:** Manage Roles

**Arguments:**
- `member` — The member to receive the role
- `role` — The role to add (mention or name)

**Example:**
```

!roleadd @User @Member

```

---

### `roleremove`
Remove a role from a member.

**Usage:** `!roleremove <member> <role>`

**Permissions:** Manage Roles

**Arguments:**
- `member` — The member to lose the role
- `role` — The role to remove (mention or name)

**Example:**
```

!roleremove @User @Muted

```

---

## Owner Commands

These commands are restricted to bot owners configured in `config.json`.

### `eval`
Execute arbitrary Python code.

**Usage:** `!eval <code>`

**Example:**
```

!eval print(len(bot.guilds))

```

---

### `load`
Load a bot extension dynamically.

**Usage:** `!load <extension>`

**Example:**
```

!load moderation.commands.custom

```

---

### `unload`
Unload a bot extension dynamically.

**Usage:** `!unload <extension>`

**Example:**
```

!unload moderation.commands.custom

```

---

### `reload`
Reload a bot extension dynamically.

**Usage:** `!reload <extension>`

**Example:**
```

!reload moderation.commands.moderation

```

---

### `shutdown`
Gracefully shut down the bot.

**Usage:** `!shutdown`

---

## Permission Hierarchy

The bot enforces Discord's role hierarchy for all moderation actions:

1. **Server Owner** — Immune to all moderation
2. **Bot Owners** — Immune to most moderation (configurable)
3. **Higher Roles** — Cannot be moderated by lower roles
4. **Bot Role** — Must be above the target's highest role

If any hierarchy check fails, the action is blocked with an explanatory message.

---

## Error Messages

| Error | Cause |
|-------|-------|
| Missing Permissions | You lack the required Discord permission |
| Bot Missing Permissions | The bot lacks the required Discord permission |
| Hierarchy Violation | Target has equal or higher role than you |
| Bot Hierarchy | Target's role is above the bot's highest role |
| Self Moderation | You cannot moderate yourself |
| Owner Immune | Target is a server or bot owner |
| Invalid Duration | Duration string is malformed or out of range |
| Invalid User | User mention/ID could not be resolved |

---

Need help with a specific command? Open a [GitHub Discussion](https://github.com/modules-gg/moderation/discussions).