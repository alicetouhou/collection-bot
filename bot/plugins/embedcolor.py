import crescent
import hikari
import re

from bot.model import Plugin

plugin = Plugin()


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx)


@plugin.include
@crescent.command(name="embedcolor", description="Set the embed color for a character in your list.")
class EmbedColorCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    color = crescent.option(
        str,
        "Choose a color to set as an embed color. This can be a RGB hex code, tuple, or [default].",
        name="color",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        if not ctx.guild_id:
            return

        user = await dbsearch.create_user(ctx.guild_id, ctx.user)
        character = await plugin.model.utils.validate_search_in_list(ctx, user, self.search)

        if character is None:
            await ctx.respond(
                f"This character does not exist."
            )
            return

        if self.color == "default":
            await character.set_embed_color("F598DF")

            await ctx.respond(
                f"You reset the default image of **{character.first_name} {character.last_name}** to the default color."
            )
            return

        hex_match_without_hashtag = re.fullmatch("[\dabcdef]{6}", self.color)
        hex_match_with_hashtag = re.fullmatch("#[\dabcdef]{6}", self.color)

        rgb_match = re.fullmatch("\(?(0*(?:[1-9][0-9]?|1[0-9][0-9]|2[0-4][0-9]|25[0-5])),(0*(?:[1-9][0-9]?|1[0-9][0-9]|2[0-4][0-9]|25[0-5])),(0*(?:[1-9][0-9]?|1[0-9][0-9]|2[0-4][0-9]|25[0-5]))\)?",
                                 self.color)

        if hex_match_without_hashtag:
            color_text = "#" + self.color.upper()
            await character.set_embed_color(self.color)

        elif hex_match_with_hashtag:
            color_text = self.color.upper()
            await character.set_embed_color(self.color[1:])

        elif rgb_match:
            red = rgb_match.group(1)
            green = rgb_match.group(2)
            blue = rgb_match.group(3)

            color = f"{int(red):x}{int(green):x}{int(blue):x}"
            color_text = "#" + color.upper()
            await character.set_embed_color(color)

        else:
            await ctx.respond(
                f"You did not pick a valid color."
            )
            return

        await ctx.respond(
            f"You set the default image of **{character.first_name} {character.last_name}** to **{color_text}**."
        )
