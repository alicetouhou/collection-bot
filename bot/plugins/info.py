import crescent
import hikari

from bot.utils import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="playerinfo", description="Show your statistics.", dm_enabled=False)
class InfoCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        utils = plugin.model.utils

        user = ctx.user if self.member is None else self.member
        claims = await utils.get_claims(ctx.guild_id, user.id)
        rolls = await utils.get_rolls(ctx.guild_id, user.id)
        character_list = await utils.get_characters(ctx.guild_id, user.id)
        currency = await utils.get_currency(ctx.guild_id, user.id)
        description = f"💛 Top character: **{character_list[0].first_name} {character_list[0].last_name}**\n📚List size: **{len(character_list)}**\n<:wishfragments:1148459769980530740> Wish Fragments: **{currency}**\n\n🥅 Claims available: **{claims}**\n🎲 Rolls available: **{rolls}**"
        embed = hikari.Embed(title=f"{user}'s Stats", color="f598df", description=description)
        if character_list:
            embed.set_thumbnail(character_list[0].images[0])
        await ctx.respond(embed)
