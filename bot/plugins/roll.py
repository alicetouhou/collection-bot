import crescent
import hikari
import miru
from bot.utils import Plugin, pick_random_character, claim_character, add_claims, get_claims, add_rolls, get_rolls, is_claimed, add_currency
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
            await ctx.respond(f"**{ctx.user.mention}** attempted to claim, but has **0** claims left!")
            return
        self.stop()
        claim_character(ctx.guild_id, ctx.user.id, self.character)
        add_claims(ctx.guild_id, ctx.user.id, -1)
        await ctx.respond(f"**{ctx.user.mention}** claimed **{self.character.first_name} {self.character.last_name}**!\nRemaining claims: **{claims-1}**")


class FragmentView(miru.View):
    character: Character

    def __init__(self, **kwargs):
        miru.View.__init__(self, timeout=kwargs['timeout'])
        self.character = kwargs['character']

    @miru.button(label=f"Claim Fragments!", emoji="<:lunar_essence:817912848784949268>", style=hikari.ButtonStyle.PRIMARY)
    async def claim_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        self.stop()
        add_currency(ctx.guild_id, ctx.user.id, self.character.value)
        await ctx.respond(f"**{ctx.user.mention}** obtained **{self.character.value}**<:lunar_essence:817912848784949268>")

@plugin.include
@crescent.command(name="roll", description="Roll a character.")
class RollCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        rolls = get_rolls(ctx.guild.id, ctx.user.id)
        if rolls <= 0:
            await ctx.respond(f"You have no rolls left! Use **/claimrolls** to claim more.")
            return
        add_rolls(ctx.guild.id, ctx.user.id, -1)
        picked_character = pick_random_character()
        claimed = is_claimed(ctx.guild.id, picked_character)

        name = picked_character.first_name + " " + picked_character.last_name
        description = f'ID `{picked_character.id}` • {picked_character.value}<:lunar_essence:817912848784949268>'
        embed = hikari.embeds.Embed(title=name, color="f598df", description=description)
        embed.set_image(picked_character.images[0])
        embed.set_image(picked_character.images[0])


        anime_list = sorted(picked_character.anime)
        manga_list = sorted(picked_character.manga)
        games_list = sorted(picked_character.games)
        animeography = ''
        count = 0
        for manga in manga_list:
            animeography += f'📖 {manga}\n' if manga != "" and count < 4 else ""
            count += 1
        for anime in anime_list:
            animeography += f'🎬 {anime}\n' if anime != "" and count < 4 else ""
            count += 1
        for game in games_list:
            animeography += f'🎮 {game}\n' if game != "" and count < 4 else ""
            count += 1
        if count >= 4:
            animeography += f'*and {count-4} more..*'

        embed.add_field(name="Appears in:", value=animeography)

        view = ClaimView(timeout=60, character=picked_character)

        if claimed:
            view = FragmentView(timeout=60, character=picked_character)

        await ctx.respond(embed, components=view)
        message = ctx.interaction.fetch_initial_response()
        await view.start(message)