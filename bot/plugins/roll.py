import typing as t

import crescent
import hikari
import miru
import asyncio
import random

from bot.character import Character
from bot.upgrades import Upgrades
from bot.model import Plugin
from bot.utils import CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE

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
        user = await plugin.model.dbsearch.create_user(ctx.guild_id, ctx.user)

        claims = user.claims
        if claims <= 0:
            await ctx.respond(
                f"**{ctx.user.mention}** attempted to claim, but has **0** claims left!\nUse **/daily** to get more, or buy them with /shop."
            )
            await self.start()
            return
        await self.on_timeout()
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
        currency = user.currency
        multiplier = user.get_upgrade_value(Upgrades.FRAGMENT_BONUS)
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


class RollCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        async def send_response(
            msg: str,
            embed: hikari.Embed,
            components: t.Sequence[hikari.api.ComponentBuilder],
            mentions: t.Sequence[int],
        ):
            return await ctx.respond(
                msg,
                embed=embed,
                components=components,
                user_mentions=mentions,
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
@crescent.command(name="roll", description="Roll a character.")
class LongCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        command = RollCommand()
        await command.callback(ctx)


@plugin.include
@crescent.command(name="r", description="Alias of /roll.")
class ShortenedCommand:
    async def callback(self, ctx: crescent.Context) -> None:
        command = RollCommand()
        await command.callback(ctx)


@plugin.include
@crescent.event
async def on_message(event: hikari.GuildMessageCreateEvent):
    if not (event.content and event.message.guild_id and (event.content.strip() == "/roll" or event.content.strip() == "/r")):
        return

    async def send_response(
        msg: str,
        embed: hikari.Embed,
        components: t.Sequence[hikari.api.ComponentBuilder],
        mentions: t.Sequence[int],
    ):
        return await event.message.respond(
            msg,
            embed=embed,
            components=components,
            user_mentions=mentions,
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
        [str, hikari.Embed, t.Sequence[hikari.api.ComponentBuilder], t.Sequence[int]],
        t.Awaitable[hikari.Message],
    ],
    send_error: t.Callable[[str], t.Awaitable[None]],
):
    if not guild_id:
        await send_error(CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE)
        return

    dbsearch = plugin.model.dbsearch

    player, picked_character = await asyncio.gather(
        dbsearch.create_user(
            guild_id, user), dbsearch.create_random_character(guild_id)
    )

    # We want to have a bigger chance for every item in the wishlist.
    # This number grows so it would be equivalent to checking a random number
    # is in bonus `len(wishlist)` times.
    bonus = player.get_upgrade_value(Upgrades.WISHLIST_RATE_BONUS)
    bonus = 1 - (1 - bonus) ** len(player.wishlist)

    if bonus and len(player.wishlist) > 0:
        random_number = random.random()
        if random_number < bonus:
            random_index = random.choice(player.wishlist)
            new_character = await dbsearch.create_character_from_id(guild_id, random_index)

            if new_character is not None:
                picked_character = new_character

    claimed, wishlist_people = await asyncio.gather(
        picked_character.get_claimed_id(),
        picked_character.get_wished_ids(),
    )

    if player.rolls <= 0:
        await send_error("You have no rolls left! Use **/getrolls** to claim more.")
        return

    wishlist_people_formatted = ""
    for id in wishlist_people:
        wishlist_people_formatted += f"<@{id}> "

    view: miru.View = ClaimView(timeout=180, character=picked_character)

    if claimed:
        view = FragmentView(timeout=180, character=picked_character)

    embed = await picked_character.get_claimable_embed()
    embed.set_footer(
        f"{player.rolls - 1} roll{'s' if player.rolls != 2 else ''} remaining")

    message = await send_response(
        wishlist_people_formatted,
        embed,
        view,
        wishlist_people,
    )

    await view.start(message)

    await player.set_rolls(player.rolls - 1)
