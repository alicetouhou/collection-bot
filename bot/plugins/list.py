import crescent
import hikari
import miru
from miru.ext import nav

from bot.character import Character
from bot.model import Plugin

plugin = Plugin()


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
                characters_on_page = character_list[count: 20 + count]

                description = header

                for character in characters_on_page:
                    if character is None:
                        break

                    description += f"`{'0' * (6 - len(str(character.character.id)))}{character.character.id}` **{character.character.first_name} {character.character.last_name}** • <:wishfragments:1148459769980530740> {character.character.value}\n"

                embed = hikari.Embed(
                    title=f"{user.name}'s Characters", color="f598df", description=description)

                if character_list[0] is None:
                    return

                embed.set_thumbnail(character_list[0].character.images[0])

                pages.append(embed)
                count += 20

            navigator = nav.NavigatorView(pages=pages)
            await navigator.send(ctx.interaction)
