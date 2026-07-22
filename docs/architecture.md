# Architecture Overview

This document describes the internal architecture of the modules.gg Moderation Module.

---

## Design Principles

1. **Separation of Concerns** — Each package has a single responsibility
2. **Dependency Inversion** — Services depend on abstractions, not concrete implementations
3. **Fail-Safe Defaults** — Missing configuration or errors do not crash the bot
4. **Extensibility** — New commands, events, and services can be added without modifying existing code

---

## Package Structure

```

moderation/
├── init.py          # Public API exports
├── bot.py               # Bot client lifecycle
├── config.py            # Configuration management
├── logger.py            # Logging subsystem
├── constants.py         # Immutable constants and enums
│
├── commands/            # User-facing commands (Cogs)
│   ├── moderation.py    # Core moderation commands
│   └── owner.py         # Owner-only commands
│
├── events/              # Discord gateway event handlers
│   ├── moderation.py    # Moderation-related events
│   └── errors.py        # Global error handling
│
├── checks/              # Permission predicates
│   └── permissions.py   # Hierarchy and permission checks
│
├── database/            # Data persistence
│   └── connection.py    # Connection pool management
│
├── models/              # Data structures
│   ├── case.py          # Case entity
│   ├── user.py          # Moderated user entity
│   └── guild.py         # Guild settings entity
│
├── services/            # Business logic
│   ├── case_service.py      # Case CRUD operations
│   ├── modlog_service.py    # Mod log channel management
│   └── user_service.py      # User record management
│
├── utilities/           # Helper functions
│   ├── converters.py    # Input parsing
│   ├── formatters.py    # Output formatting
│   └── validators.py    # Input validation
│
├── localization/        # Internationalization
│   └── strings.py       # String catalog
│
└── exceptions/          # Custom exceptions
├── base.py          # Root exception classes
├── checks.py        # Permission errors
├── commands.py      # Command errors
└── database.py      # Database errors

```

---

## Data Flow

### Command Execution

```

User invokes command
↓
discord.py parses arguments
↓
Permission checks (checks/)
↓
Command handler (commands/)
↓
Business logic (services/)
↓
Data access (database/) — v1.1
↓
Discord API call
↓
Response sent to user
↓
Event logged (events/, logger)

```

### Event Handling

```

Discord emits event
↓
Event listener (events/)
↓
Business logic (services/)
↓
Data persistence (database/) — v1.1
↓
Mod log channel update (services/modlog) — v1.1

```

---

## Key Components

### ModerationBot (`bot.py`)

Extends `discord.ext.commands.Bot`. Responsible for:
- Configuration loading
- Logging initialization
- Extension loading
- Signal handling
- Graceful shutdown

### ConfigManager (`config.py`)

Singleton pattern. Responsible for:
- JSON file parsing
- Environment variable overrides
- Validation
- Typed access via dataclasses

### ConnectionPool (`database/connection.py`)

Async-aware SQLite connection pool. Responsible for:
- Connection lifecycle
- Query execution
- Resource limiting via semaphore

### Services (`services/`)

Stateless business logic classes. Each service:
- Receives `ModerationBot` instance on init
- Operates on models
- Logs operations
- Returns results (never sends messages directly)

---

## Extension System

Extensions are loaded dynamically from `config.json`:

```json
"extensions": {
    "paths": [
        "moderation.commands",
        "moderation.events"
    ]
}
```

Each extension module must expose:

```python
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MyCog(bot))
```

Extensions can be loaded, unloaded, and reloaded at runtime via owner commands.

---

Error Handling Strategy

Layer	Error Type	Handling	
Discord API	`discord.HTTPException`	Catch, log, user-friendly message	
Permissions	`ModerationError` subclasses	Cog error handler → embed	
Validation	`ValidationError`	Immediate command response	
Database	`DatabaseError`	Log, retry or fail gracefully	
Unknown	`Exception`	Global handler, log traceback	

---

Future Architecture (v1.1+)

Case System
- `CaseService` persists to database
- `Case` model mapped to ORM/SQLite
- Case numbers are guild-scoped auto-increment

Mod Log
- `ModLogService` sends embeds to configured channel
- Per-guild configuration in `GuildSettings`

Plugin API (v1.2)
- Third-party extensions loaded from `plugins/` directory
- Hook system for custom checks and formatters

---

Need clarification on any component? Open a [GitHub Discussion](https://github.com/modules-gg/moderation/discussions).
