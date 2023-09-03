import crescent
import hikari
from bot.utils import Plugin
from bot.utils import pick_random_character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="ping", description="Ping the bot.")
class PingCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond("Pong!")