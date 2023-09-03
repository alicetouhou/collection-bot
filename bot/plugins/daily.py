import crescent
import hikari
from bot.utils import Plugin, get_daily_claimed_time, set_daily_claimed_time, add_claims
from bot.character import Character
import time

plugin = crescent.Plugin[hikari.GatewayBot, None]()

@plugin.include
@crescent.command(name="daily", description="Claim your daily rolls.")
class ListCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        last_claim_time = get_daily_claimed_time(ctx.guild.id, ctx.user.id)
        current_time = int(time.time())
        message = ""

        if current_time - last_claim_time >= 86400:
            add_claims(ctx.guild.id, ctx.user.id, 5)
            set_daily_claimed_time(ctx.guild.id, ctx.user.id, current_time)
            message = "Daily claimed! 5 rolls have been added. Next daily can be claimed in **24 hours**."
        else:
            diff = (last_claim_time + 86400) - current_time
            hours = int(diff/3600)
            minutes = int(diff/60) % 60
            message = f"You already claimed your daily! Next daily can be claimed in **{hours} hours and {minutes} minutes**."

        await ctx.respond(message)