import crescent
import hikari
from bot.character import Character
from bot.utils import Plugin, get_characters, search_characters, reorder
import random
import string
import asyncio

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="top", description="Move a character to the top of your list, which sets your thumbnail image to them.")
class TradeAddCommand:
    id = crescent.option(str, "Enter a character's ID.", name="id")
    async def callback(self, ctx: crescent.Context) -> None:
        self.id = int(self.id)
        if self.id > 2147483647 or self.id < 1:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return          
        characters = get_characters(ctx.guild.id, ctx.user.id)

        included = False
        for character in characters:
            if self.id == character.id:
                included = True

        inputted_char_id = search_characters(id=self.id, name=None, appearences=None)
        if included == False:     
            if len(inputted_char_id) == 0:
                await ctx.respond(f"{self.id} is not a valid ID!")
                return
            else:
                name = f"{inputted_char_id[0].first_name} {inputted_char_id[0].last_name}"
                await ctx.respond(f"{name} is not in your list!")
                return    

        character = inputted_char_id[0]
        reorder(ctx.guild.id, ctx.user.id, character)
        await ctx.respond(f"**{character.first_name} {character.last_name}** has been moved to the top of your list.")