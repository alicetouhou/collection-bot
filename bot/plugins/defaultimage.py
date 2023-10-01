import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx)


@plugin.include
@crescent.command(name="defaultimage", description="Set the default image for a character in your list.")
class DefaultImageCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    image_index = crescent.option(
        int,
        "Choose a page number to set as the character's default image.",
        name="image",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        if not ctx.guild_id:
            return

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character = await plugin.model.utils.validate_search_in_list(ctx, user, self.search)

        if character is None:
            await ctx.respond(
                f"This character does not exist."
            )
            return

        if self.image_index > len(character.images) or self.image_index < 1:
            await ctx.respond(
                f"You did not pick a valid image number."
            )
            return

        await character.set_default_image(self.image_index)

        await ctx.respond(
            f"You set the default image of **{character.first_name} {character.last_name}** to #{self.image_index}."
        )
