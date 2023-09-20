import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, option)


@plugin.include
@crescent.command(name="give", description="Give a character to another player.")
class GiveCommand:
    member = crescent.option(
        hikari.User, "Enter a server member's @.", name="username")
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        if not ctx.guild_id:
            return None

        user_a = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character = await plugin.model.utils.validate_search_in_list(ctx, user_a, self.search)

        if character is None:
            return

        user_b = await dbsearch.create_user(ctx.guild_id, self.member)

        description = ""
        description += f"`{character.id}` {character.first_name} {character.last_name} was traded from {ctx.user.mention} to {self.member.mention}\n"

        await ctx.respond(description)

        await user_a.remove_from_characters(character)
        await user_b.append_to_characters(character)
