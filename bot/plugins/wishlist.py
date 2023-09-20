import math

import crescent
import hikari

from bot.model import Plugin
from bot.upgrades import Upgrades
from bot.utils import guild_only

plugin = Plugin()

wishlist_group = crescent.Group("wishlist")


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_autocomplete(ctx, option)


@plugin.include
@wishlist_group.child
@crescent.hook(guild_only)
@crescent.command(name="list", description="View your or another server member's wishes.")
class WishListCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx.guild_id, ctx.user if self.member is None else self.member)

        wishlist = await user.wishlist
        wishlist_size = await user.get_upgrade_value(Upgrades.WISHLIST_SIZE)

        character_list = []
        for character_id in wishlist:
            character_instance = await dbsearch.create_character_from_id(ctx.guild_id, character_id)

            if character_instance is not None:
                character_list.append(character_instance)

        description = ""
        for character in character_list:
            description += f"`{'0' * (6 - int(math.log(character.id, 10) + 1))}{character.id}` {character.first_name} {character.last_name}\n"
        embed = hikari.Embed(title=f"{user.name}'s Characters", color="f598df", description=description)
        embed.set_footer(f"{len(character_list)}/{wishlist_size} slots full")
        await ctx.respond(embed)


@plugin.include
@wishlist_group.child
@crescent.hook(guild_only)
@crescent.command(name="add", description="Add a character to your wishlist.")
class WishAddCommand:
    search = crescent.option(
        str,
        "Enter the character's name, ID, and/or the name of series they appear in.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)

        user_character_ids = await user.wishlist
        wishlist_size = await user.get_upgrade_value(Upgrades.WISHLIST_SIZE)
        character_list = await dbsearch.create_character_from_search(ctx, self.search)

        if len(character_list) != 1:
            await ctx.respond(
                f"You may only add one character to your wishlist at a time. Make sure your search returns a unique value."
            )
            return None

        character = character_list[0]

        if character.id in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is already in your wishlist.")
            return None

        if len(user_character_ids) >= wishlist_size:
            await ctx.respond(f"You can not add more than {wishlist_size} characters to your wishlist.")
            return

        await user.append_to_wishlist(character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been added to your wishlist.")


@plugin.include
@wishlist_group.child
@crescent.hook(guild_only)
@crescent.command(name="remove", description="Remove a character from your wishlist.")
class WishRemoveCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character_list = await dbsearch.create_character_from_search(ctx, self.search)

        user_character_ids = await user.wishlist

        if len(character_list) != 1:
            await ctx.respond(
                f"You may only remove one character to your wishlist at a time. Make sure your search returns a unique value."
            )
            return None

        character = character_list[0]

        if character.id not in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your wishlist.")
            return None

        await user.remove_from_wishlist(character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been removed from your wishlist.")
