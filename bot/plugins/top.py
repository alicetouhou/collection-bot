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


async def character_search_autocomplete_6(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "sixth")


async def character_search_autocomplete_7(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "seventh")


async def character_search_autocomplete_8(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "eighth")


async def character_search_autocomplete_9(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "ninth")


async def character_search_autocomplete_10(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "tenth")


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
        default=None
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

    sixth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="sixth",
        autocomplete=character_search_autocomplete_6,
        default=None
    )

    seventh = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="seventh",
        autocomplete=character_search_autocomplete_7,
        default=None
    )

    eighth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="eighth",
        autocomplete=character_search_autocomplete_8,
        default=None
    )

    ninth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="ninth",
        autocomplete=character_search_autocomplete_9,
        default=None
    )

    tenth = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="tenth",
        autocomplete=character_search_autocomplete_10,
        default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)

        params_list = [self.tenth, self.ninth, self.eighth, self.seventh, self.sixth,
                       self.fifth, self.fourth, self.third, self.second, self.first]
        new_top_order = []

        for i in range(0, 10):
            param = params_list[i]
            if param is None:
                char = user.characters[9-i]
                if not char:
                    return
                character = await plugin.model.utils.validate_search_in_list(ctx, user, char)
                if not character:
                    continue

            else:
                character = await plugin.model.utils.validate_search_in_list(ctx, user, param)

                if not character:
                    continue

            new_top_order.append(character)

        await user.set_top_chars(new_top_order, [0, 1, 2, 3, 4, 5, 6, 7, 8, 9])

        del user
        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        top_ten_characters = await dbsearch.create_characters_from_ids(ctx.guild_id, user.characters[:10])
        description = ""

        for index, character in enumerate(top_ten_characters):
            if not character:
                continue
            description += f"{index+1}. **{character.first_name} {character.last_name}**\n"
        await ctx.respond(f"List reordered! New top {len(top_ten_characters)}:\n{description}")
