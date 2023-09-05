import crescent
import hikari
import miru
import math
from bot.utils import Plugin, get_characters
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

class ScrollButtons(miru.View):
    mctx: crescent.Context
    page_number: int = 0
    pages: list[list[Character]]
    embed: any

    def __init__(self, **kwargs):
        miru.View.__init__(self, timeout=kwargs['timeout'])
        self.mctx = kwargs['mctx']
        self.pages = kwargs['pages']
        self.embed = kwargs['embed']

    def get_description(self) -> str:
        description = ''
        for character in self.pages[self.page_number]:
            description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"
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
    member = crescent.option(hikari.User, "Enter a server member's @. If none is specified, you will be used instead.", name="username", default=None)
    async def callback(self, ctx: crescent.Context) -> None:
        user = ctx.user if self.member is None else self.member
        character_list = get_characters(ctx.guild.id, user.id)
        if len(character_list) > 1:
            description = ''
            page = []

            count = 0
            while count < len(character_list):
                page.append(character_list[count:20+count])
                character_list
                count += 20

            for character in page[0]:
                description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` **{character.first_name} {character.last_name}** • <:wishfragments:1148459769980530740> {character.value}\n"
            embed = hikari.embeds.Embed(title=f"{user}'s Characters", color="f598df", description=description)
            embed.set_footer(f"Page {1} of {len(page)}")
            if character_list:
                embed.set_thumbnail(character_list[0].images[0])

            view = ScrollButtons(timeout=60, mctx=ctx, pages=page, embed=embed)
            await ctx.respond(embed, components=view)
            message = ctx.interaction.fetch_initial_response()
            await view.start(message)