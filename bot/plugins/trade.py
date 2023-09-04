import crescent
import hikari
from bot.character import Character
from bot.utils import Plugin, get_characters, search_characters, claim_character, remove_character
import random
import string
import asyncio

plugin = crescent.Plugin[hikari.GatewayBot, None]()

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

def get_trade_embed(ctx: crescent.Context, key: str) -> None:
    trade = current_trades[key]

    embed = hikari.embeds.Embed(title=f"Trade", color="f598df", description="Add characters to trade with /tradeadd")

    breakline = "--------------------\n"

    embed.add_field(name=f"{trade.a.username}", value=breakline + character_list_str(trade.a_list), inline=True)
    embed.add_field(name=f"{trade.b.username}", value=breakline + character_list_str(trade.b_list), inline=True)

    return embed

trade_group = crescent.Group("trade")

@plugin.include
@trade_group.child
@crescent.command(name="begin", description="Start a trade with another player.")
class TradeCommand:
    member = crescent.option(hikari.User, "Enter a server member's @.", name="username")
    async def callback(self, ctx: crescent.Context) -> None:
        other_user = self.member

        if (other_user.id == ctx.user.id):
            await ctx.respond("You cannot trade with yourself!")
            return

        trade_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

        current_trades[trade_id] = Trade(ctx.user, other_user)

        await ctx.respond(f"{ctx.user.mention} started a trade with {other_user.mention}!")

        try:
            async with asyncio.timeout(120):
                await asyncio.sleep(3600)
        except TimeoutError:
            if current_trades[trade_id]:
                del current_trades[trade_id]
                await ctx.respond(f"Timed out! {ctx.user.mention}'s and {other_user.mention}'s trade was not completed within 2 minutes.")

@plugin.include
@trade_group.child
@crescent.command(name="confirm", description="Confirm your trade. Trades cannot be modified once confirmed.")
class TradeConfirmCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:   
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break

        if trade_id == "":
            await ctx.respond(f"You are not currently in a trade!")
            return
        
        current_trade = current_trades[trade_id]

        if ctx.user == current_trade.a:
            current_trade.a_confirmed = True
        else:
            current_trade.b_confirmed = True

        await ctx.respond("Trade confirmed!")

        if current_trade.a_confirmed == False or current_trade.b_confirmed == False:
            return
        
        description = f"{character_list_str(current_trade.a_list,split=',')} traded from {current_trade.a.mention} to {current_trade.b.mention}\n{character_list_str(current_trade.b_list,split=',')} traded from {current_trade.b.mention} to {current_trade.a.mention}"

        embed = hikari.embeds.Embed(title=f"Trade Complete!", color="f598df", description=description)
        
        await ctx.respond(embed)

        for character in current_trade.a_list:
            remove_character(guild=ctx.guild.id, id=current_trade.a.id, character=character)
            claim_character(guild=ctx.guild.id, id=current_trade.b.id, character=character)

        for character in current_trade.b_list:
            remove_character(guild=ctx.guild.id, id=current_trade.b.id, character=character)
            claim_character(guild=ctx.guild.id, id=current_trade.a.id, character=character)

        del current_trades[trade_id]


@plugin.include
@trade_group.child
@crescent.command(name="cancel", description="Cancel your current trade.")
class TradeConfirmCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:   
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break

        if trade_id == "":
            await ctx.respond(f"You are not currently in a trade!")
            return
        
        current_trade = current_trades[trade_id]

        del current_trades[trade_id]

@plugin.include
@trade_group.child
@crescent.command(name="add", description="Add a character to trade by ID.")
class TradeAddCommand:
    id = crescent.option(str, "Enter a character's ID.", name="id")
    async def callback(self, ctx: crescent.Context) -> None:
        self.id = int(self.id)
        if self.id > 2147483647 or self.id < 1:
            await ctx.respond(f"{self.id} is not a valid ID!")
            return          
        print(current_trades)
        characters = get_characters(ctx.guild.id, ctx.user.id)

        included = False
        for character in characters:
            if self.id == character.id:
                included = True

        if included == False:     
            inputted_char_id = search_characters(id=self.id, name=None, appearences=None)
            if len(inputted_char_id) == 0:
                await ctx.respond(f"{self.id} is not a valid ID!")
                return
            else:
                name = f"{inputted_char_id[0].first_name} {inputted_char_id[0].last_name}"
                await ctx.respond(f"{name} is not in your list!")
                return    

        # Find trade id

        id_list = current_trades.keys()
        trade_id = ""

        for trade in id_list:   
            if current_trades[trade].a.id == ctx.user.id or current_trades[trade].b.id == ctx.user.id:
                trade_id = trade
                break
        
        if trade_id == "":
            await ctx.respond(f"You are not currently in a trade!")
            return    
        
        if ctx.user == current_trades[trade_id].a:
            if current_trades[trade_id].a_confirmed == True:
                await ctx.respond("You already confirmed the trade. You can't add any more characters.")
                return
            current_trades[trade_id].a_list.append(characters[0])
        else:
            if current_trades[trade_id].b_confirmed == True:
                await ctx.respond("You already confirmed the trade. You can't add any more characters.")
                return
            current_trades[trade_id].b_list.append(characters[0])

        await ctx.respond(get_trade_embed(ctx, trade_id))