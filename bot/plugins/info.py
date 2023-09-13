import crescent
import hikari

from bot.model import Plugin

plugin = Plugin()


@plugin.include
@crescent.command(name="playerinfo", description="Show your statistics.")
class InfoCommand:
    member = crescent.option(
        hikari.User,
        "Enter a server member's @. If none is specified, you will be used instead.",
        name="username",
        default=None,
    )

    async def callback(self, ctx: crescent.Context) -> None:
        assert ctx.guild_id is not None
        dbsearch = plugin.model.dbsearch

        user = await dbsearch.create_user(ctx, ctx.user if self.member is None else self.member)

        claims = await user.claims
        rolls = await user.rolls
        character_list = await user.characters
        currency = await user.currency

        description = f'\n<:wishfragments:1148459769980530740> Wish Fragments: **{currency}**\n\n🥅 Claims available: **{claims}**\n🎲 Rolls available: **{rolls}**'
        if character_list:
            character = (await dbsearch.create_character_from_id(ctx, character_list[0])).character
            description = f'💛 Top character: **{character.first_name} {character.last_name}**\n📚 List size: **{len(character_list)}**' + description
        embed = hikari.embeds.Embed(title=f"{user.name}'s Stats", color="f598df", description=description)
        if character_list:
            embed.set_thumbnail(character.images[0])
        await ctx.respond(embed)
