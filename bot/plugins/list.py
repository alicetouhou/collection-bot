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
@crescent.command(name="list", description="List the characters you or another player currently have.")
class ListCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )
    search = crescent.option(
        str,
        "Enter the character's name, ID, and/or the name of series they appear in.",
        name="search",
        autocomplete=character_search_autocomplete,
        default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx.guild_id, ctx.user if self.member is None else self.member)
        character_list = [await dbsearch.create_character_from_id(ctx.guild_id, x) for x in await user.characters]

        if character_list[0] is None:
            return

        first_image = character_list[0].images[0]

        if self.search:
            char_filter = await dbsearch.create_character_from_search(
                ctx.guild_id, self.search, limit=100)
            new_list = filter(
                lambda char: char in char_filter, character_list)
            character_list = list(new_list)

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

                    description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` **{character.first_name} {character.last_name}** • <:wishfragments:1148459769980530740> {character.value}\n"

                embed = hikari.Embed(
                    title=f"{user.name}'s Characters", color="f598df", description=description)

                embed.set_thumbnail(first_image)

                pages.append(embed)
                count += 20

        navigator = nav.NavigatorView(pages=pages)
        await navigator.send(ctx.interaction)
