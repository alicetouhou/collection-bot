import asyncio
import random
import string

import crescent
import hikari

from bot.character import Character
from bot.model import Plugin
from bot.utils import guild_only

plugin = Plugin(command_hooks=[guild_only])


class Trade:
    a: hikari.User
    b: hikari.User

    a_list: list[Character]
    b_list: list[Character]

    a_confirmed: bool = False
    b_confirmed: bool = False

    def __init__(self, a, b):
        self.a = a
        self.b = b
        self.a_list = []
        self.b_list = []


current_trades: dict[str, Trade] = {}


def character_list_str(list: list[Character], split="\n") -> str:
    output = ""
    for character in list:
        output += f"`{character.id}` {character.first_name} {character.last_name}{split}"
    return output


def get_trade_embed(ctx: crescent.Context, key: str) -> hikari.Embed:
    trade = current_trades[key]

    embed = hikari.Embed(
        title="Trade",
        color="f598df",
        description="Add characters to trade with /tradeadd",
    )

    breakline = "--------------------\n"

    embed.add_field(
        name=f"{trade.a.username}",
        value=breakline + character_list_str(trade.a_list),
        inline=True,
    )
    embed.add_field(
        name=f"{trade.b.username}",
        value=breakline + character_list_str(trade.b_list),
        inline=True,
    )

    return embed


trade_group = crescent.Group("trade")


async def character_search_autocomplete(
    ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
) -> list[tuple[str, str]]:
    return await plugin.model.utils.character_search_in_list_autocomplete(ctx, "search")


@plugin.include
@trade_group.child
@crescent.command(name="begin", description="Start a trade with another player.")
class TradeCommand:
    member = crescent.option(
        hikari.User, "Enter a server member's @.", name="username")

    async def callback(self, ctx: crescent.Context) -> None:
        other_user = self.member

        if other_user.id == ctx.user.id:
            await ctx.respond("You cannot trade with yourself!")
            return

        trade_id = "".join(random.choices(
            string.ascii_uppercase + string.digits, k=10))

        current_trades[trade_id] = Trade(ctx.user, other_user)

        await ctx.respond(f"{ctx.user.mention} started a trade with {other_user.mention}!")

        await asyncio.sleep(180)

        if current_trades[trade_id]:
            del current_trades[trade_id]
            await ctx.respond(
                f"Timed out! {ctx.user.mention}'s and {other_user.mention}'s trade was not completed within 3 minutes."
            )


@plugin.include
@trade_group.child
@crescent.command(
    name="confirm",
    description="Confirm your trade. Trades cannot be modified once confirmed.",
)
class TradeConfirmCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id
        dbsearch = plugin.model.dbsearch

        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break

        if trade_id == "":
            await ctx.respond("You are not currently in a trade!")
            return

        current_trade = current_trades[trade_id]

        if ctx.user == current_trade.a:
            current_trade.a_confirmed = True
        else:
            current_trade.b_confirmed = True

        await ctx.respond("Trade confirmed!")

        if current_trade.a_confirmed is False or current_trade.b_confirmed is False:
            return

        user_a = await dbsearch.create_user(ctx.guild_id, current_trade.a)
        user_b = await dbsearch.create_user(ctx.guild_id, current_trade.b)

        description = ""
        if len(current_trade.a_list) >= 1:
            description += f"{character_list_str(current_trade.a_list,split=',')} traded from {current_trade.a.mention} to {current_trade.b.mention}\n"
        if len(current_trade.b_list) >= 1:
            description += f"{character_list_str(current_trade.b_list,split=',')} traded from {current_trade.b.mention} to {current_trade.a.mention}"

        embed = hikari.Embed(title="Trade Complete!",
                             color="f598df", description=description)

        await ctx.respond(embed)

        for character in current_trade.a_list:
            await user_a.remove_from_characters(character)
            await user_b.append_to_characters(character)

        for character in current_trade.b_list:
            await user_b.remove_from_characters(character)
            await user_a.append_to_characters(character)

        del current_trades[trade_id]


@plugin.include
@trade_group.child
@crescent.command(name="cancel", description="Cancel your current trade.")
class TradeCancelCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break

        if trade_id == "":
            await ctx.respond("You are not currently in a trade!")
            return

        del current_trades[trade_id]
        await ctx.respond("Your trade has been cancelled.")


@plugin.include
@trade_group.child
@crescent.command(name="add", description="Add a character to trade by ID.")
class TradeAddCommand:
    search = crescent.option(
        str,
        "Search for a character by name, or ID. The given and family names can be in any order.",
        name="search",
        autocomplete=character_search_autocomplete,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id

        utils = plugin.model.utils
        dbsearch = plugin.model.dbsearch
        user = await dbsearch.create_user(ctx.guild_id, ctx.user)

        # Find trade id
        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break

        if trade_id == "":
            await ctx.respond("You are not currently in a trade!")
            return

        character_list = await dbsearch.create_character_from_search(ctx.guild_id, self.search)

        if len(character_list) != 1:
            await ctx.respond(
                "You may only add one character to trade at a time. Make sure your search returns a unique value."
            )
            return

        character = await utils.validate_id_in_list(ctx, user, character_list[0].id)

        if character is None:
            return

        if ctx.user == current_trades[trade_id].a:
            if current_trades[trade_id].a_confirmed is True:
                await ctx.respond("You already confirmed the trade. You can't add any more characters.")
                return
            current_trades[trade_id].a_list.append(character)
        else:
            if current_trades[trade_id].b_confirmed is True:
                await ctx.respond("You already confirmed the trade. You can't add any more characters.")
                return
            current_trades[trade_id].b_list.append(character)

        await ctx.respond(get_trade_embed(ctx, trade_id))
