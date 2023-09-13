import os

import crescent

from bot.model import Plugin

plugin = Plugin()

admin_group = crescent.Group("admin")


@plugin.include
@admin_group.child
@crescent.command(
    name="populate",
    description="Add characters to database from file.",
    guild=int(os.environ["GUILD"]),
)
async def populate(ctx: crescent.Context):
    await ctx.respond("`Running command to add characters....`")
    await plugin.model.utils.add_characters_to_db()
    await ctx.respond("`Characters added!`")
