import random

import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(
    name="coinflip",
    description="Wager an amount. If the coin flips heads, your wager doubles.",
)
class InfoCommand:
    wager = crescent.option(
        int,
        "Wager an amount. If heads, your wager doubles. If tails, you loose it.",
        name="wager",
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        currency = await user.currency

        if self.wager > currency:
            await ctx.respond(
                "You do not have enough <:wishfragments:1148459769980530740> wish fragments to make that wager. Try gambling more! Maybe you can reach the number you want faster 🙂"
            )
            return

        flip = "heads" if random.randint(0, 1) == 1 else "tails"

        if flip == "heads":
            await user.set_currency(currency + self.wager)
            await ctx.respond(
                f"Congrats! I flipped heads, and your wager doubled from **<:wishfragments:1148459769980530740>{self.wager}** to **<:wishfragments:1148459769980530740>{self.wager * 2}**. You now have <:wishfragments:1148459769980530740>**{currency + self.wager}** wish fragments"
            )
        else:
            await user.set_currency(currency - self.wager)
            await ctx.respond(
                f"Too bad! I flipped tails. You just lost your wager of **<:wishfragments:1148459769980530740>{self.wager}**. You now have <:wishfragments:1148459769980530740> {currency - self.wager} wish fragments. You should try gambling more to make back what you lost."
            )
