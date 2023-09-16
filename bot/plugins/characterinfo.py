import crescent
import hikari
import miru
from miru.ext import nav

from bot.character import Character
from bot.model import Plugin

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_autocomplete(ctx, option)


@plugin.include
@crescent.command(name="search", description="Search for a character.")
class ListCommand:
    search = crescent.option(
        str,
        "Enter the character's name, ID, and/or the name of series they appear in.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        character_list = await plugin.model.dbsearch.create_character_from_search(ctx, self.search)

        if len(character_list) > 1:
            header = f"Multiple characters fit your query. Please narrow your search or search by ID.\nquery: `{self.search}`\n\n"
            pages = []

            count = 0
            while count < len(character_list):
                characters_on_page = character_list[count: 20 + count]

                description = header

                for character in characters_on_page:
                    description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"

                embed = hikari.Embed(title="Search results",
                                     color="f598df", description=description)

                pages.append(embed)
                count += 20

            navigator = nav.NavigatorView(pages=pages)
            await navigator.send(ctx.interaction)

        elif len(character_list) == 0:
            await ctx.respond("No results were found for your query!")
            return
        else:
            character = character_list[0]

            navigator = character.get_navigator()
            await navigator.send(ctx.interaction)
