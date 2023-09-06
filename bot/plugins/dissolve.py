import crescent

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="dissolve", description="Turn a character into wish fragments.", dm_enabled=False)
class DissolveCommand:
    id = crescent.option(int, "Enter a character's ID.", name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

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

        await utils.add_currency(ctx.guild_id, ctx.user.id, character.value)
        await utils.remove_character(ctx.guild_id, ctx.user.id, character)
        await ctx.respond(
            f"You turned **{character.first_name} {character.last_name}** into <:wishfragments:1148459769980530740> {character.value} wish fragments. In additon, they are now claimable by any player."
        )
