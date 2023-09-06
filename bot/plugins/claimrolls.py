import time

import crescent

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(
    name="getrolls",
    description="Get your rolls. One roll regenerates every 15 minutes, and 30 can be stored until regeration stops.",
    dm_enabled=False,
)
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        last_claim_time = await utils.get_daily_rolls_time(ctx.guild_id, ctx.user.id)
        current_time = int(time.time())
        message = ""

        stockpile = int((current_time - last_claim_time) / 60 / 15)

        if (last_claim_time) == 0:
            stockpile = 10
            await utils.set_daily_rolls_time(ctx.guild_id, ctx.user.id, current_time)
            await utils.add_rolls(ctx.guild_id, ctx.user.id, stockpile)
            regenerate_time = 900
            rolls_to_be_claimed = 10
        else:
            rolls_to_be_claimed = min(stockpile, 30)
            last_regeneration = last_claim_time + stockpile * 900
            regenerate_time = 900 - (current_time - last_regeneration)
            await utils.add_rolls(ctx.guild_id, ctx.user.id, rolls_to_be_claimed)
            await utils.set_daily_rolls_time(ctx.guild_id, ctx.user.id, last_regeneration)
        message = f"{rolls_to_be_claimed} rolls have been claimed.\nNext roll regenerates in: **{int(regenerate_time/60)}** minutes and **{regenerate_time % 60}** seconds"

        await ctx.respond(message)
