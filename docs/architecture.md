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

├── README.md                 # This file
├── LICENSE                   # MIT License
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── CODE_OF_CONDUCT.md        # Community standards
├── SECURITY.md               # Security policy and reporting
├── requirements.txt          # Runtime dependencies
├── pyproject.toml            # Build system and tool configuration
├── .gitignore                # Git ignore rules
├── config.example.json       # Example configuration
├── docs/                     # Documentation
├── moderation/               # Main package
│   ├── __init__.py           # Package initialization
│   ├── bot.py                # Bot client and lifecycle
│   ├── config.py             # Configuration management
│   ├── logger.py             # Logging setup
│   ├── constants.py          # Constants and enums
│   ├── commands/             # Slash commands and prefix commands
│   ├── events/               # Event listeners
│   ├── checks/               # Permission and validation checks
│   ├── database/             # Database models and connections
│   ├── models/               # Data models and dataclasses
│   ├── services/             # Business logic services
│   ├── utilities/            # Helper functions and utilities
│   ├── localization/         # i18n strings and translations
│   └── exceptions/           # Custom exceptions
├── tests/                    # Test suite
└── scripts/                  # 

```

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
