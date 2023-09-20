import typing as t

import crescent
import hikari
import miru
import asyncio
import random

from bot.character import Character
from bot.upgrades import Upgrades
from bot.model import Plugin

plugin = Plugin()


class ClaimView(miru.View):
    character: Character

    def __init__(self, *, timeout: float, character: Character) -> None:
        super().__init__(timeout=timeout)
        self.character = character

    @miru.button(label="Claim!", emoji="❗", style=hikari.ButtonStyle.PRIMARY)
    async def claim_button(self, button: miru.Button, ctx: miru.ViewContext) -> None:
        assert ctx.guild_id, "This command can not be used in DMs"

        self.stop()
        await self.on_timeout()
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        claims = await user.claims
        if claims <= 0:
            await ctx.respond(
                f"**{ctx.user.mention}** attempted to claim, but has **0** claims left!\nUse **/daily** to get more, or buy them with /shop."
            )
            return
        await user.append_to_characters(self.character)
        await user.set_claims(claims - 1)
        await ctx.respond(
            f"**{ctx.user.mention}** claimed **{self.character.first_name} {self.character.last_name}**!\nRemaining claims: **{claims-1}**"
        )

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message is None:
            return
        await self.message.edit(components=self)


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
        assert ctx.guild_id, "This command can not be used in DMs."

        self.stop()
        await self.on_timeout()
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        currency = await user.currency
        multiplier = await user.get_upgrade_value(Upgrades.FRAGMENT_BONUS)
        await user.set_currency(currency + int(self.character.value * multiplier))
        description = f"**{ctx.user.mention}** obtained **{self.character.value}**<:wishfragments:1148459769980530740>"
        if multiplier > 1:
            description = f"**{ctx.user.mention}** obtained **{int(self.character.value * multiplier)}**<:wishfragments:1148459769980530740> (Multiplier bonus)"
        await ctx.respond(description)

    async def on_timeout(self) -> None:
        for item in self.children:
            item.disabled = True
        if self.message is None:
            return
        await self.message.edit(components=self)


@plugin.include
@crescent.command(name="roll", description="Roll a character.")
class RollCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        async def send_response(
            msg: str,
            embed: hikari.Embed,
            components: t.Sequence[hikari.api.ComponentBuilder],
        ):
            return await ctx.respond(
                msg,
                embed=embed,
                components=components,
                user_mentions=[ctx.user],
                ensure_message=True,
            )

        async def send_error(msg: str) -> None:
            await ctx.respond(msg)

        await roll_command(
            ctx.guild_id,
            ctx.user,
            send_response,
            send_error,
        )


@plugin.include
@crescent.event
async def on_message(event: hikari.GuildMessageCreateEvent):
    if not (event.content and event.message.guild_id and event.content.strip() == "/roll"):
        return

    async def send_response(
        msg: str,
        embed: hikari.Embed,
        components: t.Sequence[hikari.api.ComponentBuilder],
    ):
        return await event.message.respond(
            msg,
            embed=embed,
            components=components,
            user_mentions=[event.author_id],
        )

    async def send_error(msg: str) -> None:
        await event.message.respond(msg)

    await roll_command(
        event.message.guild_id,
        event.message.author,
        send_response,
        send_error,
    )


async def roll_command(
    guild_id: hikari.Snowflake | None,
    user: hikari.User,
    send_response: t.Callable[
        [str, hikari.Embed, t.Sequence[hikari.api.ComponentBuilder]],
        t.Awaitable[hikari.Message],
    ],
    send_error: t.Callable[[str], t.Awaitable[None]],
):
    if not guild_id:
        await send_error("You must in a guild to use this command.")
        return

    guild = plugin.app.cache.get_guild(guild_id) or await plugin.app.rest.fetch_guild(guild_id)

    dbsearch = plugin.model.dbsearch

    user, picked_character = await asyncio.gather(
        dbsearch.create_user(guild.id, user), dbsearch.create_random_character(guild)
    )

    rolls, bonus, claimed, wishlist_people = await asyncio.gather(
        user.rolls,
        user.get_upgrade_value(Upgrades.WISHLIST_RATE_BONUS),
        picked_character.get_claimed_id(),
        picked_character.get_wished_ids(),
    )

    if bonus:
        random_number = random.random()
        if random_number < bonus:
            wishlist = await user.wishlist
            random_index = random.choice(wishlist)
            new_character = await dbsearch.create_character_from_id(guild, random_index)

            if new_character is not None:
                picked_character = new_character
                wishlist_people = await picked_character.get_wished_ids()

    if rolls <= 0:
        await send_error("You have no rolls left! Use **/getrolls** to claim more.")
        return

    wishlist_people_formatted = ""
    for id in wishlist_people:
        wishlist_people_formatted += f"<@{id}> "

    view: miru.View = ClaimView(timeout=180, character=picked_character)

    if claimed:
        view = FragmentView(timeout=180, character=picked_character)

    embed = await picked_character.get_claimable_embed()
    embed.set_footer(f"{rolls - 1} roll{'s' if rolls != 2 else ''} remaining")

    message = await send_response(
        wishlist_people_formatted,
        embed,
        view,
    )
    await view.start(message)

    await user.set_rolls(rolls - 1)
