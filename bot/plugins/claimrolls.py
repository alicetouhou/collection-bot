import time

import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(
    name="getrolls",
    description="Get your rolls. One roll regenerates every 15 minutes, and 30 can be stored until regeration stops.",
)
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx, ctx.user)

        last_claim_time = await user.rolls_claimed_time
        current_time = int(time.time())
        message = ""

        stockpile = int((current_time - last_claim_time) / 60 / 15)

        if (last_claim_time) == 0:
            stockpile = 10
            await user.set_rolls_claimed_time(current_time)
            await user.set_rolls((await user.rolls) + stockpile)
            regenerate_time = 900
            rolls_to_be_claimed = 10
        else:
            rolls_to_be_claimed = min(stockpile, 30)
            last_regeneration = last_claim_time + stockpile * 900
            regenerate_time = 900 - (current_time - last_regeneration)
            await user.set_rolls_claimed_time(last_regeneration)
            await user.set_rolls((await user.rolls) + rolls_to_be_claimed)
        message = f"{rolls_to_be_claimed} rolls have been claimed.\nNext roll regenerates in: **{int(regenerate_time/60)}** minutes and **{regenerate_time % 60}** seconds"

        await ctx.respond(message)
