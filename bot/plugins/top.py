import crescent

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(
    name="top",
    description="Move a character to the top of your list, which sets your thumbnail image to them.",
)
class TradeAddCommand:
    id = crescent.option(int, "Enter a character's ID.", name="id")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        if self.id > 2147483647 or self.id < 1:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return
        characters = await utils.get_characters(ctx.guild_id, ctx.user.id)

        included = False
        for character in characters:
            if self.id == character.id:
                included = True

        inputted_char_id = await utils.search_characters(id=self.id, name=None, appearances=None)
        if included is False:
            if not inputted_char_id:
                await ctx.respond(f"{self.id} is not a valid ID!")
                return
            else:
                name = f"{inputted_char_id[0].first_name} {inputted_char_id[0].last_name}"
                await ctx.respond(f"{name} is not in your list!")
                return

        character = inputted_char_id[0]
        await utils.reorder(ctx.guild_id, ctx.user.id, character)
        await ctx.respond(f"**{character.first_name} {character.last_name}** has been moved to the top of your list.")
