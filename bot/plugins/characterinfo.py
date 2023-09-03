import crescent
import hikari
from bot.utils import Plugin, search_characters
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="characterinfo", description="Show your statistics.")
class ListCommand:
    id_search = crescent.option(str, "Search for a character by ID.", name="id", default=None)
    first_name_search = crescent.option(str, "Search for a character by first name.", name="firstname", default=None)
    last_name_search = crescent.option(str, "Search for a character by last name.", name="lastname", default=None)
    appearances_search = crescent.option(str, "Search for a character by anime appearances.", name="appearances", default=None)
    async def callback(self, ctx: crescent.Context) -> None:
        character_list = search_characters(id=self.id_search, first_name=self.first_name_search,last_name=self.last_name_search, appearences=self.appearances_search)

        if len(character_list) > 1:
            description = 'Multiple characters fit your query. Please narrow your search or search by ID.\n\n'
            for character in character_list:
                description += f"`{'0' * (6 - len(str(character.id)))}{character.id}` {character.first_name} {character.last_name}\n"
            embed = hikari.embeds.Embed(title=f"Search results", color="f598df", description=description)
            await ctx.respond(embed)
        else:
            character = character_list[0]
            name = character.first_name + " " + character.last_name
            description = f'{character.value}<:lunar_essence:817912848784949268>'

            embed = hikari.embeds.Embed(title=name, color="f598df", description=description)

            embed.set_image(character.images[0])


            anime_list = sorted(character.anime)
            animeography = ''
            for anime in anime_list:
                animeography += f'🎬 {anime}\n'

            embed.add_field(name="Appears in:", value=animeography)

            await ctx.respond(embed)