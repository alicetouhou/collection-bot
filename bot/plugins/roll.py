import crescent
import hikari
import miru
from bot.utils import Plugin, pick_random_character, claim_character, add_claims, get_claims
from bot.character import Character

plugin = crescent.Plugin[hikari.GatewayBot, None]()

class ClaimView(miru.View):
    character: Character

    def __init__(self, **kwargs):
        miru.View.__init__(self, timeout=kwargs['timeout'])
        self.character = kwargs['character']

    @miru.button(label="Claim!", emoji="❗", style=hikari.ButtonStyle.PRIMARY)
    async def claim_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        claims = get_claims(ctx.guild_id, ctx.user.id)
        if (claims <= 0):
            await ctx.respond(f"**{ctx.user}** attempted to claim, but has **0** claims left!")
            return
        self.stop()
        clicker = ctx.user.id
        claim_character(ctx.guild_id, ctx.user.id, self.character)
        add_claims(ctx.guild_id, ctx.user.id, -1)
        await ctx.respond(f"**{ctx.user}** claimed **{self.character.first_name} {self.character.last_name}**!\nRemaining claims: **{claims-1}**")

@plugin.include
@crescent.command(name="roll", description="Roll a character.")
class RollCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        picked_character = pick_random_character()
        name = picked_character.first_name + " " + picked_character.last_name
        description = f'{", ".join(picked_character.anime)} • {picked_character.value}<:lunar_essence:817912848784949268>'
        embed = hikari.embeds.Embed(title=name, color="f598df", description=description)
        embed.set_image(picked_character.images[0])

        view = ClaimView(timeout=60, character=picked_character)  # Create a new view
        await ctx.respond(embed, components=view)
        message = ctx.interaction.fetch_initial_response()
        await view.start(message)