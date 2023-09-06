import crescent
import hikari
import miru

from bot.character import Character
from bot.utils import Plugin

plugin = Plugin()


class ClaimView(miru.View):
    character: Character

    def __init__(self, *, timeout: float, character: Character) -> None:
        super().__init__(timeout=timeout)
        self.character = character

    @miru.button(label="Claim!", emoji="❗", style=hikari.ButtonStyle.PRIMARY)
    async def claim_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        claims = await utils.get_claims(ctx.guild_id, ctx.user.id)
        if claims <= 0:
            await ctx.respond(
                f"**{ctx.user.mention}** attempted to claim, but has **0** claims left!\nUse **/daily** to get more, or buy them with /shop."
            )
            return
        await utils.claim_character(ctx.guild_id, ctx.user.id, self.character)
        await utils.add_claims(ctx.guild_id, ctx.user.id, -1)
        await ctx.respond(
            f"**{ctx.user.mention}** claimed **{self.character.first_name} {self.character.last_name}**!\nRemaining claims: **{claims-1}**"
        )
        self.stop()


class FragmentView(miru.View):
    character: Character

    def __init__(self, **kwargs):
        miru.View.__init__(self, timeout=kwargs["timeout"])
        self.character = kwargs["character"]

    @miru.button(
        label="Claim Fragments!",
        emoji="<:wishfragments:1148459769980530740>",
        style=hikari.ButtonStyle.PRIMARY,
    )
    async def claim_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        assert ctx.guild_id is not None
        self.stop()
        await plugin.model.utils.add_currency(ctx.guild_id, ctx.user.id, self.character.value)
        await ctx.respond(
            f"**{ctx.user.mention}** obtained **{self.character.value}**<:wishfragments:1148459769980530740>"
        )


@plugin.include
@crescent.command(name="roll", description="Roll a character.")
class RollCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        rolls = await utils.get_rolls(ctx.guild_id, ctx.user.id)
        if rolls <= 0:
            await ctx.respond("You have no rolls left! Use **/getrolls** to claim more.")
            return
        picked_character = await utils.pick_random_character()
        claimed = utils.is_claimed(ctx.guild_id, picked_character)

        name = picked_character.first_name + " " + picked_character.last_name
        description = f"ID `{picked_character.id}` • {picked_character.value}<:wishfragments:1148459769980530740>"
        embed = hikari.Embed(title=name, color="f598df", description=description)
        embed.set_image(picked_character.images[0])
        embed.set_image(picked_character.images[0])

        anime_list = sorted(picked_character.anime)
        manga_list = sorted(picked_character.manga)
        games_list = sorted(picked_character.games)
        animeography = ""
        count = 0
        for manga in manga_list:
            animeography += f"📖 {manga}\n" if manga != "" and count < 4 else ""
            count += 1
        for anime in anime_list:
            animeography += f"🎬 {anime}\n" if anime != "" and count < 4 else ""
            count += 1
        for game in games_list:
            animeography += f"🎮 {game}\n" if game != "" and count < 4 else ""
            count += 1
        if count >= 4:
            animeography += f"*and {count-4} more..*"

        embed.add_field(name="Appears in:", value=animeography)
        embed.set_footer(f"{rolls-1} rolls remaining")

        wishlist_people = await utils.get_users_who_wished(ctx.guild_id, picked_character)

        wishlist_people_formatted = ""
        for id in wishlist_people:
            wishlist_people_formatted += f"<@{id}> "

        view: miru.View = ClaimView(timeout=180, character=picked_character)

        if claimed:
            view = FragmentView(timeout=180, character=picked_character)

        await ctx.respond(
            wishlist_people_formatted,
            embed=embed,
            components=view,
            user_mentions=wishlist_people,
        )
        message = ctx.interaction.fetch_initial_response()
        await view.start(message)

        await utils.add_rolls(ctx.guild_id, ctx.user.id, -1)
