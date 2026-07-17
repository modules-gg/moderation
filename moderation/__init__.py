"""modules.gg Moderation Module v1 Remake.

A production-ready Discord moderation system built with discord.py 2.x.
This package provides the core bot infrastructure, configuration management,
logging, and extension loading capabilities.

Example:
    Run the bot from the command line::

        $ python -m moderation

    Or import and run programmatically::

        from moderation import ModerationBot
        bot = ModerationBot()
        bot.run()

Attributes:
    __version__: The current version of the moderation module.
    __author__: The author of the moderation module.
    __license__: The license under which the module is distributed.

"""

from __future__ import annotations

from moderation.bot import ModerationBot

__version__ = "0.1.0"
__author__ = "modules.gg"
__license__ = "MIT"
__all__ = ["ModerationBot", "__version__", "__author__", "__license__"]
