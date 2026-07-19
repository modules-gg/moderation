"""Discord event listeners for the moderation module.

This package contains all bot event handlers, organized by functional area.
Events are implemented as discord.py Cogs and loaded dynamically
via the extension loader.

Each submodule should expose a ``setup`` function for discord.py::

    async def setup(bot: commands.Bot) -> None:
        await bot.add_cog(SomeEventCog(bot))

"""

from __future__ import annotations

__all__: list[str] = []
