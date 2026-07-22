# Configuration Guide

This document explains all configuration options for the modules.gg Moderation Bot.

---

## Configuration File

The bot reads from `config.json` in the project root. Copy `config.example.json` to get started:

```bash
cp config.example.json config.json
```

---

Top-Level Sections

Section	Description	
`bot`	Discord bot settings	
`logging`	Logging subsystem configuration	
`extensions`	Extension loading settings	
`database`	Database connection settings	

---

`bot` Section

`token` (string, required)
Your Discord bot token. Get this from the [Discord Developer Portal](https://discord.com/developers/applications).

```json
"token": "YOUR_BOT_TOKEN_HERE"
```

> Security: Never commit this token. It is equivalent to a password.

---

`prefix` (string)
The command prefix for prefix-based commands. Default: `"!"`

```json
"prefix": "!"
```

---

`owner_ids` (array of integers)
Discord user IDs with owner-level privileges. These users can use owner-only commands like `eval` and `shutdown`.

```json
"owner_ids": [123456789012345678, 987654321098765432]
```

---

`description` (string)
The bot's description shown in help and profile. Default: `"modules.gg Moderation Bot"`

```json
"description": "My Custom Moderation Bot"
```

---

`activity` (object)
The bot's presence activity displayed in the member list.

```json
"activity": {
    "type": "watching",
    "text": "over the community"
}
```

Supported types: `playing`, `streaming`, `listening`, `watching`, `competing`

---

`intents` (object)
Discord gateway intents the bot requests. All default to `false` unless specified.

```json
"intents": {
    "guilds": true,
    "members": true,
    "moderation": true,
    "messages": true,
    "message_content": true,
    "reactions": true,
    "voice_states": false,
    "presences": false
}
```

Intent	Required For	
`guilds`	Basic server operations	
`members`	User lookups, join/leave events	
`moderation`	Timeout events, audit log	
`messages`	Message events, purge	
`message_content`	Reading message content	
`reactions`	Reaction events	
`voice_states`	Voice channel features (not used)	
`presences`	Presence/activity tracking (not used)	

---

`logging` Section

`level` (string)
Minimum log level. One of: `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`. Default: `"INFO"`

```json
"level": "INFO"
```

---

`format` (string)
Log message format string using Python's logging format specifiers.

```json
"format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
```

---

`date_format` (string)
Timestamp format string.

```json
"date_format": "%Y-%m-%d %H:%M:%S"
```

---

`file` (object)
File logging configuration.

```json
"file": {
    "enabled": true,
    "path": "logs/moderation.log",
    "max_bytes": 10485760,
    "backup_count": 5
}
```

Option	Description	Default	
`enabled`	Whether to log to file	`false`	
`path`	Log file path	`"logs/moderation.log"`	
`max_bytes`	Max file size before rotation (bytes)	`10485760` (10 MiB)	
`backup_count`	Number of backup files to keep	`5`	

---

`console` (object)
Console logging configuration.

```json
"console": {
    "enabled": true,
    "use_colors": true
}
```

Option	Description	Default	
`enabled`	Whether to log to console	`true`	
`use_colors`	Whether to use ANSI colors	`true`	

---

`extensions` Section

`auto_load` (boolean)
Whether to fail startup if an extension fails to load. Default: `true`

```json
"auto_load": true
```

If `false`, the bot will log warnings but continue starting even if extensions fail.

---

`paths` (array of strings)
Dotted module paths to load as extensions on startup.

```json
"paths": [
    "moderation.commands",
    "moderation.events"
]
```

---

`database` Section

`type` (string)
Database type. Currently only `sqlite` is supported. Default: `"sqlite"`

```json
"type": "sqlite"
```

---

`connection_string` (string)
Database connection URI.

```json
"connection_string": "sqlite:///data/moderation.db"
```

For SQLite, the path is relative to the project root.

---

Environment Variable Overrides

Any configuration value can be overridden via environment variables using the format:

```
MODERATION_SECTION_KEY=value
```

Examples:

```bash
# Override bot token
MODERATION_BOT_TOKEN=your_token_here

# Override log level
MODERATION_LOGGING_LEVEL=DEBUG

# Override prefix
MODERATION_BOT_PREFIX=?
```

Environment variables take precedence over `config.json` values.

---

Complete Example

```json
{
    "bot": {
        "token": "YOUR_BOT_TOKEN",
        "prefix": "!",
        "owner_ids": [123456789012345678],
        "description": "My Moderation Bot",
        "activity": {
            "type": "watching",
            "text": "over the community"
        },
        "intents": {
            "guilds": true,
            "members": true,
            "moderation": true,
            "messages": true,
            "message_content": true,
            "reactions": false,
            "voice_states": false,
            "presences": false
        }
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        "date_format": "%Y-%m-%d %H:%M:%S",
        "file": {
            "enabled": true,
            "path": "logs/moderation.log",
            "max_bytes": 10485760,
            "backup_count": 5
        },
        "console": {
            "enabled": true,
            "use_colors": true
        }
    },
    "extensions": {
        "auto_load": true,
        "paths": [
            "moderation.commands",
            "moderation.events"
        ]
    },
    "database": {
        "type": "sqlite",
        "connection_string": "sqlite:///data/moderation.db"
    }
}
```

---

Troubleshooting

Issue	Solution	
Changes not applied	Restart the bot (hot-reload not yet implemented)	
Invalid JSON	Validate with `python -m json.tool config.json`	
Token not working	Regenerate in Discord Developer Portal	
Logs not appearing	Check `logging.level` is not set too high	

---

Need help? Open a [GitHub Discussion](https://github.com/modules-gg/moderation/discussions).
