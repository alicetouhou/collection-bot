import math

import crescent
import hikari

from bot.utils import Plugin

plugin = Plugin()

wishlist_group = crescent.Group("wishlist")


@plugin.include
@wishlist_group.child
@crescent.command(name="list", description="View your or another server member's wishes.")
class WishListCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        user = ctx.user if self.member is None else self.member
        character_list = await utils.get_wishes(ctx.guild_id, user.id)
        description = ""
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.Embed(title=f"{user}'s Characters", color="f598df", description=description)
        embed.set_footer(f"{len(character_list)}/7 slots full")
        await ctx.respond(embed)


@plugin.include
@wishlist_group.child
@crescent.command(name="add", description="Add a character to your wishlist.")
class WishAddCommand:
    id = crescent.option(int, "Enter a character's ID.", name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        inputted_char_id = await utils.search_characters(id=self.id, name=None, appearances=None)
        if len(inputted_char_id) == 0:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return

        wishes = await utils.get_wishes(ctx.guild_id, ctx.user.id)
        character = inputted_char_id[0]
        wish_ids = [character.id for character in wishes]

        if character.id in wish_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is already in your wishlist.")
            return

        if len(wishes) >= 7:
            await ctx.respond("You can not add more than 7 characters to your wishlist.")
            return

        await utils.add_wish(ctx.guild_id, ctx.user.id, character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been added to your wishlist.")


@plugin.include
@wishlist_group.child
@crescent.command(name="remove", description="Remove a character from your wishlist.")
class WishRemoveCommand:
    id = crescent.option(int, "Enter a character's ID.", name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        inputted_char_id = await utils.search_characters(id=self.id, name=None, appearances=None)
        if len(inputted_char_id) == 0:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return

        wishes = await utils.get_wishes(ctx.guild_id, ctx.user.id)
        character = inputted_char_id[0]
        wish_ids = [character.id for character in wishes]

        if character.id not in wish_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your wishlist.")
            return

        await utils.remove_wish(ctx.guild_id, ctx.user.id, character)
        await ctx.respond(f"**{character.first_name} {character.last_name}** has been removed from your wishlist.")
