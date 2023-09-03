import crescent
import hikari
import math
from bot.utils import Plugin, get_characters
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="list", description="List the characters you currently have.")
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        character_list = get_characters(ctx.guild.id, ctx.user.id)
        description = ''
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.embeds.Embed(title=f"{ctx.user}'s Characters", color="f598df", description=description)
        await ctx.respond(embed)