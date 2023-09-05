import crescent
import hikari
import math
from bot.utils import Plugin, get_characters, get_wishes, add_wish, remove_wish, search_characters

plugin = crescent.Plugin[hikari.GatewayBot, None]()

wishlist_group = crescent.Group("wishlist")

@plugin.include
@wishlist_group.child
@crescent.command(name="list", description="View your or another server member's wishes.")
class WishListCommand:
    member = crescent.option(hikari.User, "Enter a server member's @. If none is specified, you will be used instead.", name="username", default=None)
    async def callback(self, ctx: crescent.Context) -> None:
        user = ctx.user if self.member is None else self.member
        character_list = get_wishes(ctx.guild.id, user.id)
        description = ''
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.embeds.Embed(title=f"{user}'s Characters", color="f598df", description=description)
        embed.set_footer(f"{len(character_list)}/7 slots full")
        await ctx.respond(embed)

@plugin.include
@wishlist_group.child
@crescent.command(name="add", description="Add a character to your wishlist.")
class WishAddCommand:
    id = crescent.option(str, "Enter a character's ID.", name="id")
    async def callback(self, ctx: crescent.Context) -> None:
        self.id = int(self.id)
        if self.id > 2147483647 or self.id < 1:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return       
                   
        inputted_char_id = search_characters(id=self.id, name=None, appearences=None)
        if len(inputted_char_id) == 0:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return
        
        wishes = get_wishes(ctx.guild.id, ctx.user.id)
        character = inputted_char_id[0]
        wish_ids = [character.id for character in wishes]
        
        if character.id in wish_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is already in your wishlist.")
            return
        
        if len(wishes) >= 7:
            await ctx.respond(f"You can not add more than 7 characters to your wishlist.")
            return          
        
        add_wish(ctx.guild.id, ctx.user.id, character)
        
        await ctx.respond(f"**{character.first_name} {character.last_name}** has been added to your wishlist.")

@plugin.include
@wishlist_group.child
@crescent.command(name="remove", description="Remove a character from your wishlist.")
class WishRemoveCommand:
    id = crescent.option(str, "Enter a character's ID.", name="id")
    async def callback(self, ctx: crescent.Context) -> None:
        self.id = int(self.id)
        if self.id > 2147483647 or self.id < 1:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return       
                   
        inputted_char_id = search_characters(id=self.id, name=None, appearences=None)
        if len(inputted_char_id) == 0:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return
        
        wishes = get_wishes(ctx.guild.id, ctx.user.id)
        character = inputted_char_id[0]
        wish_ids = [character.id for character in wishes]
        
        if not character.id in wish_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your wishlist.")
            return
       
        remove_wish(ctx.guild.id, ctx.user.id, character)
        await ctx.respond(f"**{character.first_name} {character.last_name}** has been removed from your wishlist.")

