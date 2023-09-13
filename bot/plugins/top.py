import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(
    name="top",
    description="Move a character to the top of your list, which sets your thumbnail image to them.",
)
class TopCommand:
    id = crescent.option(int, "Enter a character's ID.", name="id")

    async def callback(self, ctx: crescent.Context) -> None:
        user = await plugin.model.dbsearch.create_user(ctx, ctx.user)
        val = await plugin.model.utils.validate_id_in_list(ctx, user, self.id)
        if not val:
            return

        await user.reorder(val)

        await ctx.respond(f"**{val.first_name} {val.last_name}** has been moved to the top of your list.")
