import crescent
import hikari
import miru
from miru.ext import nav

from bot.character import Character
from bot.model import Plugin

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
        description = ""
        for character in self.pages[self.page_number]:
            description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` **{character.first_name} {character.last_name}** • <:wishfragments:1148459769980530740> {character.value}\n"
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


@plugin.include
@crescent.command(name="list", description="List the characters you or another player currently have.")
class ListCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx, ctx.user if self.member is None else self.member)
        character_list = [await dbsearch.create_character_from_id(ctx, x) for x in await user.characters]

        if len(character_list) >= 1:
            header = ""
            pages = []

            count = 0
            while count < len(character_list):
                characters_on_page = character_list[count : 20 + count]

                description = header

                for character in characters_on_page:
                    description += f"`{'0' * (6 - len(str(character.character.id)))}{character.character.id}` **{character.character.first_name} {character.character.last_name}** • <:wishfragments:1148459769980530740> {character.character.value}\n"

                embed = hikari.Embed(title=f"{user.name}'s Characters", color="f598df", description=description)
                embed.set_thumbnail(character_list[0].character.images[0])

                pages.append(embed)
                count += 20

            navigator = nav.NavigatorView(pages=pages)
            await navigator.send(ctx.interaction)
