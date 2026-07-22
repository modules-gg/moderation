# Getting Started

This guide will walk you through setting up and running the modules.gg Moderation Bot.

---

## Prerequisites

- Python 3.11 or higher
- A Discord account and access to the [Discord Developer Portal](https://discord.com/developers/applications)
- `git` installed on your system

---

## Step 1: Create a Discord Bot

1. Go to the [Discord Developer Portal](https://discord.com/developers/applications)
2. Click **New Application** and give it a name
3. Navigate to **Bot** in the left sidebar
4. Click **Add Bot**
5. Under **Privileged Gateway Intents**, enable:
   - **Server Members Intent**
   - **Message Content Intent**
   - **Moderation Intent**
6. Copy your **Token** (you will need this later)

---

## Step 2: Invite the Bot to Your Server

1. Navigate to **OAuth2 > URL Generator**
2. Under **Scopes**, select `bot` and `applications.commands`
3. Under **Bot Permissions**, select:
   - Kick Members
   - Ban Members
   - Moderate Members
   - Manage Messages
   - Manage Channels
   - Manage Nicknames
   - Manage Roles
   - Read Message History
   - Send Messages
   - Embed Links
   - Use Slash Commands
4. Copy the generated URL and open it in your browser
5. Select your server and authorize the bot

---

## Step 3: Install the Bot

```bash
# Clone the repository
git clone https://github.com/modulesgg/moderation-module.git
cd moderation-module

# Create a virtual environment
python -m venv venv

# Activate the environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

---

Step 4: Configure the Bot

```bash
# Copy the example configuration
cp config.example.json config.json

# Edit config.json with your settings
# Replace YOUR_DISCORD_BOT_TOKEN_HERE with your actual bot token
```

Your `config.json` should look like this:

```json
{
    "bot": {
        "token": "YOUR_ACTUAL_BOT_TOKEN",
        "prefix": "!",
        "owner_ids": [YOUR_DISCORD_USER_ID]
    },
    "logging": {
        "level": "INFO"
    }
}
```

> Security Warning: Never commit `config.json` or share your bot token. It is equivalent to a password.

---

Step 5: Run the Bot

```bash
python -m moderation
```

You should see output similar to:

```
2026-07-22 11:04:00 | INFO     | moderation.bot | Starting ModerationBot v0.1.0...
2026-07-22 11:04:01 | INFO     | moderation.bot | Bot is online and ready!
2026-07-22 11:04:01 | INFO     | moderation.bot | Logged in as: YourBotName (ID: 123456789012345678)
```

---

Next Steps

- Read the [Commands Reference](./commands.md) for available commands
- Read the [Configuration Guide](./configuration.md) for advanced settings
- Read the [Permissions Guide](./permissions.md) for role hierarchy setup

---

Troubleshooting

Issue	Solution	
`Configuration file not found`	Ensure `config.json` exists in the project root	
`Invalid bot token`	Verify your token in the Discord Developer Portal	
`Missing Permissions`	Check that your bot has the required OAuth2 scopes	
`ModuleNotFoundError`	Run `pip install -r requirements.txt` again	

---

Need help? Open a [GitHub Discussion](https://github.com/modulesgg/moderation/discussions).