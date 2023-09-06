import os
import crescent
import hikari
from bot.utils import add_characters_to_db, search_characters

plugin = crescent.Plugin[hikari.GatewayBot, None]()

admin_group = crescent.Group("admin")
admin_group.guild_id = guild=int(os.environ["GUILD"])

@plugin.include
@admin_group.child
@crescent.command(name="populate", description="Add characters to database from file.")
async def populate(ctx: crescent.Context):
    await ctx.respond("`Running command to add characters....`")
    add_characters_to_db()
    await ctx.respond("`Characters added!`")
