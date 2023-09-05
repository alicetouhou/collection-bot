import crescent
import hikari
from bot.utils import Plugin, add_currency, get_characters, search_characters, remove_character
from bot.character import Character
import random

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="dissolve", description="Turn a character into wish fragments.")
class DissolveCommand:
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
    
        add_currency(ctx.guild.id, ctx.user.id, character.value)
        remove_character(ctx.guild.id, ctx.user.id, character)
        await ctx.respond(f"You turned **{character.first_name} {character.last_name}** into <:wishfragments:1148459769980530740> {character.value} wish fragments. In additon, they are now claimable by any player.")