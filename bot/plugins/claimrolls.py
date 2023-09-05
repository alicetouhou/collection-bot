import crescent
import hikari
from bot.utils import Plugin, set_daily_rolls_time, get_daily_rolls_time, add_rolls, get_rolls
from bot.character import Character
import time

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="getrolls", description="Get your rolls. One roll regenerates every 15 minutes, and 30 can be stored until regeration stops.")
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        last_claim_time = get_daily_rolls_time(ctx.guild.id, ctx.user.id)
        current_time = int(time.time())
        message = ""

        stockpile = int((current_time - last_claim_time) / 60 / 15)

        if (last_claim_time) == 0:
            stockpile = 10
            set_daily_rolls_time(ctx.guild.id, ctx.user.id, current_time)
            add_rolls(ctx.guild.id, ctx.user.id, stockpile)
            regenerate_time = 900
            rolls_to_be_claimed = 10
        else:
            rolls_to_be_claimed = min(stockpile,30)
            last_regeneration = last_claim_time + stockpile * 900
            regenerate_time = 900 - (current_time - last_regeneration)
            add_rolls(ctx.guild.id, ctx.user.id, rolls_to_be_claimed)
            set_daily_rolls_time(ctx.guild.id, ctx.user.id, last_regeneration)
        message = f"{rolls_to_be_claimed} rolls have been claimed.\nNext roll regenerates in: **{int(regenerate_time/60)}** minutes and **{regenerate_time % 60}** seconds"

        await ctx.respond(message)