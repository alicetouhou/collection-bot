import crescent
import hikari
from bot.utils import Plugin, get_claims, get_rolls, get_currency, get_characters
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="playerinfo", description="Show your statistics.")
class InfoCommand:
    member = crescent.option(hikari.User, "Enter a server member's @. If none is specified, you will be used instead.", name="username", default=None)
    async def callback(self, ctx: crescent.Context) -> None:
        user = ctx.user if self.member is None else self.member
        claims = get_claims(ctx.guild.id, user.id)
        rolls = get_rolls(ctx.guild.id, user.id)
        character_list = get_characters(ctx.guild.id, user.id)
        currency = get_currency(ctx.guild.id, user.id)
        description = f'Total claims: **{claims}**\nNumber of rolls: {rolls}\nWishstone Fragments: {currency}'
        embed = hikari.embeds.Embed(title=f"{user}'s Stats", color="f598df", description=description)
        if character_list:
            embed.set_thumbnail(character_list[0].images[0])
        await ctx.respond(embed)