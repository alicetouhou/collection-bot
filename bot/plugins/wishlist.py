import math

import crescent
import hikari

from bot.model import Plugin
from bot.upgrades import Upgrades

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
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx, ctx.user if self.member is None else self.member)

        wishlist = await user.wishlist
        wishlist_size = await user.get_upgrade_value(Upgrades.WISHLIST_SIZE)

        character_list = []
        for character_id in wishlist:
            character_instance = await dbsearch.create_character_from_id(ctx, character_id)

            if character_instance is not None:
                character_list.append(character_instance.character)

        description = ""
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.Embed(
            title=f"{user.name}'s Characters", color="f598df", description=description)
        embed.set_footer(f"{len(character_list)}/{wishlist_size} slots full")
        await ctx.respond(embed)


@plugin.include
@wishlist_group.child
@crescent.command(name="add", description="Add a character to your wishlist.")
class WishAddCommand:
    id = crescent.option(int, "Enter a character's ID.",
                         name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx, ctx.user)
        selected_character = await dbsearch.create_character_from_id(ctx, self.id)

        user_character_ids = await user.wishlist
        wishlist_size = await user.get_upgrade_value(Upgrades.WISHLIST_SIZE)

        if not selected_character:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return None

        character = selected_character.character

        if self.id in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is already in your wishlist.")
            return None

        if len(user_character_ids) >= wishlist_size:
            await ctx.respond(f"You can not add more than {wishlist_size} characters to your wishlist.")
            return

        await user.append_to_wishlist(character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been added to your wishlist.")


@plugin.include
@wishlist_group.child
@crescent.command(name="remove", description="Remove a character from your wishlist.")
class WishRemoveCommand:
    id = crescent.option(int, "Enter a character's ID.",
                         name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx, ctx.user)
        selected_character = await dbsearch.create_character_from_id(ctx, self.id)

        user_character_ids = await user.wishlist

        if not selected_character:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return None

        character = selected_character.character

        if self.id not in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your wishlist.")
            return None

        await user.remove_from_wishlist(character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been removed from your wishlist.")
