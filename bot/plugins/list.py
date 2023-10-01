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
    ctx.options["search"] = ctx.options["filter"]
    return await plugin.model.utils.character_search_autocomplete(ctx, include_series=True)


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
        name="filter",
        autocomplete=character_search_autocomplete,
        default=None
    )
    order = crescent.option(
        str,
        "[default]: list order, [value]: ordered by fragment amount",
        name="order",
        default=None
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx.guild_id, ctx.user if self.member is None else self.member)

        characters = await user.characters
        character_list = await dbsearch.create_characters_from_ids(ctx.guild_id, characters, order_by=self.order)

        first_character = await dbsearch.create_character_from_id(ctx.guild_id, characters[0])

        if first_character is None:
            return

        if first_character:
            default_image = await first_character.get_default_image()
            if default_image:
                first_image = first_character.images[default_image]
            else:
                first_image = first_character.images[0]

        query_string = ""

        if self.search:
            char_filter = await dbsearch.create_character_from_search(
                ctx.guild_id, self.search, limit=100)
            new_list = filter(
                lambda char: char in char_filter, character_list)
            character_list = list(new_list)
            query_string = f"filter: `{self.search}`\n"

        if len(character_list) >= 1:
            header = f"List size: **{len(character_list)}**\n" + \
                query_string + "\n"
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
            return

        embed = hikari.Embed(
            title=f"{user.name}'s Characters", color="f598df", description=query_string)

        embed.set_thumbnail(first_image)
        await ctx.respond(embed)
