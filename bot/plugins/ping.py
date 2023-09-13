import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="ping", description="Ping the bot.")
class PingCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        await ctx.respond(f"Pong! `{round(plugin.app.heartbeat_latency * 1000)}ms`")
