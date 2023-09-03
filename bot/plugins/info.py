import crescent
import hikari
from bot.utils import Plugin, get_characters, get_claims, get_daily_claimed_time
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="playerinfo", description="Show your statistics.")
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        claims = get_claims(ctx.guild.id, ctx.user.id)
        description = f'Total claims: **{claims}**'
        embed = hikari.embeds.Embed(title=f"{ctx.user}'s Stats", color="f598df", description=description)
        await ctx.respond(embed)