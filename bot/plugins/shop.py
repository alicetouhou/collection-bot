import crescent
import hikari

from bot.utils import Plugin

plugin = Plugin()

shop_group = crescent.Group("shop")


@shop_group.child
@plugin.include
@crescent.command(name="view", description="View the shop.", dm_enabled=False)
class ViewCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        description = "🎲 Buy a roll: **500<:wishfragments:1148459769980530740>** • `/shop buy roll`\n"
        description += "🥅 Buy a claim: **2,000<:wishfragments:1148459769980530740>** • `/shop buy claim`\n"
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


@shop_group.child
@plugin.include
@crescent.command(name="buy", description="Buy an item.", dm_enabled=False)
class BuyCommand:
    item = crescent.option(str, "Select an item to purchase.", name="item")

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        if self.item not in ["roll", "claim"]:
            await ctx.respond(f"**{self.item}** is not a valid item!")

        currency = await utils.get_currency(ctx.guild_id, ctx.user.id)

        if self.item == "roll" and currency >= 500:
            await utils.add_currency(ctx.guild_id, ctx.user.id, -500)
            await utils.add_rolls(ctx.guild_id, ctx.user.id, 1)
            await ctx.respond(
                f"You purchased a **roll**!\n<:wishfragments:1148459769980530740> Wish fragments remaining: **{currency-500}**"
            )
            return

        elif self.item == "claim" and currency >= 2000:
            await utils.add_currency(ctx.guild_id, ctx.user.id, -2000)
            await utils.add_claims(ctx.guild_id, ctx.user.id, 1)
            await ctx.respond(
                f"You purchased a **claim**!\n<:wishfragments:1148459769980530740> Wish fragments remaining: **{currency-2000}**"
            )
            return

        await ctx.respond(
            "You do not have enough <:wishfragments:1148459769980530740> wish fragments to purchase that item."
        )
