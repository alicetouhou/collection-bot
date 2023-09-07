import os

import crescent

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command
async def version(ctx: crescent.Context):
    version = os.environ.get("version", "Not in production")
    await ctx.respond(f"`{version}`")
