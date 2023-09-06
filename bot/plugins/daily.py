import random
import time

import crescent

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="daily", description="Claim your daily character claims.", dm_enabled=False)
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        last_claim_time = await utils.get_daily_claimed_time(ctx.guild_id, ctx.user.id)
        current_time = int(time.time())
        message = ""

        if current_time - last_claim_time >= 86400:
            wishfragment_number = random.randint(350, 600)
            await utils.add_claims(ctx.guild_id, ctx.user.id, 5)
            await utils.set_daily_claimed_time(ctx.guild_id, ctx.user.id, current_time)
            message = f"Daily claimed! **5** claims have been added to your inventory, as well as <:wishfragments:1148459769980530740> **{wishfragment_number}** wish fragments. Next daily can be claimed in **24 hours**."
        else:
            diff = (last_claim_time + 86400) - current_time
            hours = int(diff / 3600)
            minutes = int(diff / 60) % 60
            message = (
                f"You already claimed your daily! Next daily can be claimed in **{hours} hours and {minutes} minutes**."
            )

        await ctx.respond(message)
