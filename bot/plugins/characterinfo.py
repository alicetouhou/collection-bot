import crescent
import hikari
import miru

from bot.character import Character
from bot.utils import Plugin

plugin = Plugin()


class ScrollButtons(miru.View):
    mctx: crescent.Context
    page_number: int = 0
    pages: list[list[Character]]
    embed: hikari.Embed

    def __init__(self, **kwargs):
        super().__init__(timeout=kwargs["timeout"])
        self.mctx = kwargs["mctx"]
        self.pages = kwargs["pages"]
        self.embed = kwargs["embed"]

    def get_description(self) -> str:
        description = "Multiple characters fit your query. Please narrow your search or search by ID.\n\n"
        for character in self.pages[self.page_number]:
            description += (
                f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"
            )
        return description

    @miru.button(label="", emoji="⬅️", style=hikari.ButtonStyle.SECONDARY)
    async def left_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.page_number = (self.page_number - 1) % len(self.pages)
        new_description = self.get_description()
        self.embed.description = new_description
        self.embed.set_footer(f"Page {self.page_number+1} of {len(self.pages)}")
        await self.mctx.edit(self.embed)

    @miru.button(label="", emoji="➡️", style=hikari.ButtonStyle.SECONDARY)
    async def right_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.page_number = (self.page_number + 1) % len(self.pages)
        new_description = self.get_description()
        self.embed.description = new_description
        self.embed.set_footer(f"Page {self.page_number+1} of {len(self.pages)}")
        await self.mctx.edit(self.embed)


class ImageButtons(miru.View):
    mctx: crescent.Context
    page_number: int = 0
    pages: list[str]
    embed: hikari.Embed

    def __init__(self, **kwargs):
        super().__init__(timeout=kwargs["timeout"])
        self.mctx = kwargs["mctx"]
        self.pages = kwargs["pages"]
        self.embed = kwargs["embed"]

    @miru.button(label="", emoji="⬅️", style=hikari.ButtonStyle.SECONDARY)
    async def left_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.page_number = (self.page_number - 1) % len(self.pages)
        self.embed.set_image(self.pages[self.page_number])
        self.embed.set_footer(f"Image {self.page_number+1} of {len(self.pages)}")
        await self.mctx.edit(self.embed)

    @miru.button(label="", emoji="➡️", style=hikari.ButtonStyle.SECONDARY)
    async def right_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.page_number = (self.page_number + 1) % len(self.pages)
        self.embed.set_image(self.pages[self.page_number])
        self.embed.set_footer(f"Image {self.page_number+1} of {len(self.pages)}")
        await self.mctx.edit(self.embed)


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
            description = "Multiple characters fit your query. Please narrow your search or search by ID.\n\n"
            page = []

            count = 0
            while count < len(character_list):
                page.append(character_list[count : 20 + count])
                count += 20

            for character in page[0]:
                description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"
            embed = hikari.Embed(title="Search results", color="f598df", description=description)
            embed.set_footer(f"Page {1} of {len(page)}")

            view: miru.View = ScrollButtons(timeout=180, mctx=ctx, pages=page, embed=embed)
            resp = await ctx.respond(embed, components=view)
            await view.start(resp)

        elif len(character_list) == 0:
            await ctx.respond("No results were found for your query!")
            return
        else:
            character = character_list[0]
            name = character.first_name + " " + character.last_name
            description = f"ID `{character.id}` • {character.value}<:wishfragments:1148459769980530740>"

            embed = hikari.Embed(title=name, color="f598df", description=description)

            embed.set_image(character.images[0])

            anime_list = sorted(character.anime)
            manga_list = sorted(character.manga)
            games_list = sorted(character.games)
            animeography = ""
            count = 0
            for manga in manga_list:
                animeography += f"📖 {manga}\n" if manga != "" and count < 4 else ""
                count += 1
            for anime in anime_list:
                animeography += f"🎬 {anime}\n" if anime != "" and count < 4 else ""
                count += 1
            for game in games_list:
                animeography += f"🎮 {game}\n" if game != "" and count < 4 else ""
                count += 1
            if count >= 4:
                animeography += f"*and {count-4} more..*"

            embed.add_field(name="Appears in:", value=animeography)
            embed.set_footer(f"Image {1} of {len(character.images)}")

            view = ImageButtons(timeout=180, mctx=ctx, pages=character.images, embed=embed)
            resp = await ctx.respond(embed, components=view)
            await view.start(resp)
