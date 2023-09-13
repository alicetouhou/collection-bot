import asyncio
import random
import string

import crescent
import hikari

from bot.character import Character
from bot.model import Plugin

plugin = Plugin()
@plugin.include
@crescent.command(name="give", description="Give a character to another player.")
class GiveCommand:
    member = crescent.option(hikari.User, "Enter a server member's @.", name="username")
    id = crescent.option(int, "Enter a character's ID.", name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx, ctx.user)
        character = await plugin.model.utils.validate_id_in_list(ctx, user, self.id)

        if character is None:
            return


        user_a = await dbsearch.create_user(ctx, ctx.user)
        user_b = await dbsearch.create_user(ctx, self.member)

        description = ""
        description += f"`{character.id}` {character.first_name} {character.last_name} traded from {ctx.user.mention} to {self.member.mention}\n"

        await ctx.respond(description)

        await user_a.remove_from_characters(character)
        await user_b.append_to_characters(character)


