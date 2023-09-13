import crescent
import hikari
import miru
from miru.ext import nav

from bot.character import Character
from bot.model import Plugin

plugin = Plugin()

async def autocomplete_response(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    options = ctx.options
    character_list = await plugin.model.utils.search_characters(
        name=options["name"], id=None, appearances=None, limit=10, fuzzy=True
    )
    output = []
    for character in character_list:
        name = f"{character.first_name} {character.last_name}"
        if len(name) > 100:
            name = name[0:98] + "..."
        output.append((name, name))
    return output


@plugin.include
@crescent.command(name="characterinfo", description="Search for a character.")
class ListCommand:
    id_search = crescent.option(int, "Search for a character by ID.", name="id", default=None, min_value=1)
    name_search = crescent.option(
        str,
        "Search for a character by name. The given and family names can be in any order.",
        name="name",
        default=None,
        autocomplete=autocomplete_response,
    )
    appearances_search = crescent.option(
        str,
        "Search for a character by anime appearances.",
        name="appearances",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        if self.id_search is None and self.name_search is None and self.appearances_search is None:
            await ctx.respond("At least one field must be filled out to search for a character.")
            return

        character_list = await plugin.model.utils.search_characters(
            id=self.id_search,
            name=self.name_search,
            appearances=self.appearances_search,
        )

        if len(character_list) > 1:

            query_arr = []
            if self.name_search:
                query_arr.append(f"name: {self.name_search}")
            if self.appearances_search:
                query_arr.append(f"appearances: {self.appearances_search}")

            header = f"Multiple characters fit your query. Please narrow your search or search by ID.\nquery: `{', '.join(query_arr)}`\n\n"
            pages = []

            count = 0
            while count < len(character_list):
                characters_on_page = character_list[count : 20 + count]

                description = header

                for character in characters_on_page:
                    description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"

                embed = hikari.Embed(title="Search results", color="f598df", description=description)

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
