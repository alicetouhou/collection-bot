import random
import time

import crescent

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="daily", description="Claim your daily character claims.")
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx, ctx.user)

        last_claim_time = await user.daily_claimed_time
        current_time = int(time.time())
        message = ""

        if current_time - last_claim_time >= 86400:
            wishfragment_number = random.randint(350, 600)
            current_claims = await user.claims
            await user.set_claims(current_claims + 5)
            await user.set_daily_claimed_time(current_time)
            message = f"Daily claimed! **5** claims have been added to your inventory, as well as <:wishfragments:1148459769980530740> **{wishfragment_number}** wish fragments. Next daily can be claimed in **24 hours**."
        else:
            diff = (last_claim_time + 86400) - current_time
            hours = int(diff / 3600)
            minutes = int(diff / 60) % 60
            message = (
                f"You already claimed your daily! Next daily can be claimed in **{hours} hours and {minutes} minutes**."
            )

        await ctx.respond(message)
