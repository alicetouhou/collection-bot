import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()

shop_group = crescent.Group("shop")


@shop_group.child
@plugin.include
@crescent.command(name="view", description="View the shop.")
class ViewCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        description = "🎲 Buy a roll: **250<:wishfragments:1148459769980530740>** • `/shop buy roll`\n"
        description += "🥅 Buy a claim: **900<:wishfragments:1148459769980530740>** • `/shop buy claim`\n"
        description += "\n\n*More items coming soon!*"
        embed = hikari.Embed(title="⛩️ Suzunaan Store", color="f598df", description=description)
        await ctx.respond(embed)


async def autocomplete_response(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple]:
    return [
        ("claim", "claim"),
        ("roll", "roll"),
    ]

"""Todo: fix shop buy"""
@shop_group.child
@plugin.include
@crescent.command(name="buy", description="Buy an item.")
class BuyCommand:
    item = crescent.option(str, "Select an item to purchase.", name="item")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        user = await plugin.model.dbsearch.create_user(ctx, ctx.user)

        if self.item not in ["roll", "claim"]:
            await ctx.respond(f"**{self.item}** is not a valid item!")

        currency = await user.currency

        if self.item == "roll" and currency >= 250:
            await user.set_currency(currency - 250)
            rolls = await user.rolls
            await user.set_rolls(rolls + 1)
            await ctx.respond(
                f"You purchased a **roll**!\n<:wishfragments:1148459769980530740> Wish fragments remaining: **{currency-250}**"
            )
            return

        elif self.item == "claim" and currency >= 900:
            await user.set_currency(currency - 900)
            claims = await user.claims
            await user.set_claims(claims + 1)
            await ctx.respond(
                f"You purchased a **claim**!\n<:wishfragments:1148459769980530740> Wish fragments remaining: **{currency-900}**"
            )
            return

        await ctx.respond(
            "You do not have enough <:wishfragments:1148459769980530740> wish fragments to purchase that item."
        )
