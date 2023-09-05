import os
import crescent
import hikari

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command
async def version(ctx: crescent.Context):
    version = os.environ.get('version', 'Not in production')
    await ctx.respond(f"`{version}`")
