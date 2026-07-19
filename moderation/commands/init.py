"""Discord command extensions for the moderation module.

This package contains all bot commands, organized by functional area.
Commands are implemented as discord.py Cogs and loaded dynamically
via the extension loader.

Each submodule should expose a ``setup`` function for discord.py::

    async def setup(bot: commands.Bot) -> None:
        await bot.add_cog(SomeCog(bot))

"""

from __future__ import annotations

__all__: list[str] = []
