import crescent
import hikari

from bot.model import Plugin
from bot.shop_item import shop_items
from bot.utils import guild_only

plugin = Plugin(command_hooks=[guild_only])

shop_group = crescent.Group("shop")


@shop_group.child
@plugin.include
@crescent.command(name="view", description="View the shop.")
class ViewCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        description = "Use `/shop buy item name` to buy items.\n\n"
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        for item in shop_items:
            description += item.description_line() + "\n"
        description += "\n"

        upgrades = await user.get_upgrade_shop_objects()

        for item in upgrades:
            description += item.description_line() + "\n"

        description += "\n\n*More items coming soon!*"
        embed = hikari.Embed(title="⛩️ Suzunaan Store", color="f598df", description=description)
        await ctx.respond(embed)


async def autocomplete_response(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, int]]:
    if not ctx.guild_id:
        return []
    options = ctx.options
    user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
    upgrades = await user.get_upgrade_shop_objects()
    combined_list = list(shop_items) + upgrades
    output = [(item.name, index) for index, item in enumerate(combined_list)]
    filtered_list = filter(lambda x: options["item"].lower() in x[0].lower(), output)
    return list(filtered_list)


@shop_group.child
@plugin.include
@crescent.command(name="buy", description="Buy an item.")
class BuyCommand:
    item = crescent.option(int, "Select an item to purchase.", name="item", autocomplete=autocomplete_response)

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        upgrades = await user.get_upgrade_shop_objects()
        combined_list = list(shop_items) + upgrades

        if self.item > len(combined_list) - 1 or self.item < 0:
            await ctx.respond(f"**{self.item}** is not a valid item!")
            return

        currency = await user.currency
        selected_item = combined_list[self.item]

        if currency >= selected_item.price:
            purchased = await selected_item.purchased(ctx, user)
            if purchased:
                await user.set_currency(currency - selected_item.price)

            return

        await ctx.respond(
            f"You do not have enough <:wishfragments:1148459769980530740> wish fragments to purchase {selected_item.article()} {selected_item.cased_name()}."
        )
