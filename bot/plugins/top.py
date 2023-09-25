import crescent
import hikari

from bot.model import Plugin
from bot.utils import guild_only

plugin = Plugin()


async def character_search_autocomplete_1(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "first")


async def character_search_autocomplete_2(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "second")


async def character_search_autocomplete_3(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "third")


async def character_search_autocomplete_4(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "fourth")


async def character_search_autocomplete_5(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "fifth")


@plugin.include
@crescent.hook(guild_only)
@crescent.command(
    name="top",
    description="Move a character to the top of your list, which sets your thumbnail image to them.",
)
class TopCommand:
    first = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="first",
        autocomplete=character_search_autocomplete_1,
    )

    second = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="second",
        autocomplete=character_search_autocomplete_2,
        default=None
    )

    third = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="third",
        autocomplete=character_search_autocomplete_3,
        default=None
    )

    fourth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="fourth",
        autocomplete=character_search_autocomplete_4,
        default=None
    )

    fifth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="fifth",
        autocomplete=character_search_autocomplete_5,
        default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character_list = await user.characters

        params_list = [self.fifth, self.fourth,
                       self.third, self.second, self.first]

        for param in params_list:
            if not param:
                continue

            character = await plugin.model.utils.validate_search_in_list(ctx, user, param)

            if not character:
                continue

            await user.move_to_top(character)

        if not self.second and not self.third and not self.fourth and not self.fifth:
            character = await plugin.model.utils.validate_search_in_list(ctx, user, self.first)
            if not character:
                return
            await ctx.respond(f"**{character.first_name} {character.last_name}** has been moved to the top of your list.")
        else:
            character_list = await user.characters
            top_five_characters = [await dbsearch.create_character_from_id(ctx.guild_id, char) for char in character_list[:5]]
            description = ""

            for index, character in enumerate(top_five_characters):
                if not character:
                    continue
                description += f"{index+1}. **{character.first_name} {character.last_name}**\n"
            await ctx.respond(f"List reordered! New top {len(top_five_characters)}:\n{description}")
