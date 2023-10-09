import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx)


@plugin.include
@crescent.command(name="dissolve", description="Turn a character into wish fragments.")
class DissolveCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        if not ctx.guild_id:
            return

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character = await plugin.model.utils.validate_search_in_list(ctx, user, self.search)

        if character is None:
            return

        await user.set_currency(user.currency + character.value)
        await user.remove_from_characters(character)
        await ctx.respond(
            f"You turned **{character.first_name} {character.last_name}** into <:wishfragments:1148459769980530740> {character.value} wish fragments. In additon, they are now claimable by any player."
        )
