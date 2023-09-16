import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="dissolve", description="Turn a character into wish fragments.")
class DissolveCommand:
    id = crescent.option(int, "Enter a character's ID.",
                         name="id", min_value=1, max_value=2147483647)

    async def callback(self, ctx: crescent.Context) -> None:
        dbsearch = plugin.model.dbsearch

        character = (await dbsearch.create_character_from_id(ctx, self.id))
        user = await dbsearch.create_user(ctx, ctx.user)

        user_character_ids = await user.characters

        if not character:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return

        if self.id not in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your list!")
            return

        current_currency = await user.currency
        await user.set_currency(current_currency + character.value)
        await user.remove_from_characters(character)
        await ctx.respond(
            f"You turned **{character.first_name} {character.last_name}** into <:wishfragments:1148459769980530740> {character.value} wish fragments. In additon, they are now claimable by any player."
        )
