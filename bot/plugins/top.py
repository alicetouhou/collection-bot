import crescent
import hikari

from bot.model import Plugin
from bot.utils import guild_only

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, option)


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="top",
    description="Move a character to the top of your list, which sets your thumbnail image to them.",
)
class TopCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        character = await plugin.model.utils.validate_search_in_list(ctx, user, self.search)

        if not character:
            return

        await user.reorder(character)

        await ctx.respond(f"**{character.first_name} {character.last_name}** has been moved to the top of your list.")
