import crescent
import hikari
import math
from bot.utils import Plugin, get_characters

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="list", description="List the characters you or another player currently have.")
class ListCommand:
    member = crescent.option(hikari.User, "Enter a server member's @. If none is specified, you will be used instead.", name="username", default=None)
    async def callback(self, ctx: crescent.Context) -> None:
        user = ctx.user if self.member is None else self.member
        character_list = get_characters(ctx.guild.id, user.id)
        description = ''
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.embeds.Embed(title=f"{user}'s Characters", color="f598df", description=description)
        await ctx.respond(embed)