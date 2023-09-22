import crescent
import hikari
import io
import aiohttp
import asyncio

from PIL import Image

from bot.upgrades import Upgrades
from bot.model import Plugin

plugin = Plugin()
MASK_IMAGE = Image.open('bot/data/mask.png').convert('L')


async def open_image_from_char_id(ctx: crescent.Context, character_id: int) -> io.BytesIO | None:
    if not ctx.guild_id:
        return None

    try:
        character = await plugin.model.dbsearch.create_character_from_id(ctx.guild_id, character_id)

        if character is None:
            return None

        image_url = character.images[0]
        async with aiohttp.ClientSession() as session:
            async with session.get(url=image_url) as response:
                resp = await response.read()
                image = io.BytesIO(resp)
                return image
    except:
        return None


@plugin.include
@crescent.command(name="profile", description="Show your, or another server member's, profile.")
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

        if not ctx.guild_id:
            return

        user = await dbsearch.create_user(ctx.guild_id, ctx.user if self.member is None else self.member)

        claims, rolls, character_list, currency, upgrades = await asyncio.gather(
            user.claims,
            user.rolls,
            user.characters,
            user.currency,
            user.upgrades
        )

        description = f'\n<:wishfragments:1148459769980530740> Wish Fragments: **{currency}**\n\n🥅 Claims available: **{claims}**\n🎲 Rolls available: **{rolls}**'
        if character_list:

            character = await dbsearch.create_character_from_id(ctx.guild_id, character_list[0])

            if character is None:
                return

            description = f'💛 Top character: **{character.first_name} {character.last_name}**\n📚 List size: **{len(character_list)}**' + \
                description
        embed = hikari.embeds.Embed(
            title=f"{user.name}'s Stats", color="f598df", description=description)
        if character_list:
            character_images = await asyncio.gather(
                *map(lambda x: open_image_from_char_id(ctx, x), character_list[:5]
                     ))

            filtered_chararacter_images = filter(
                lambda item: item is not None, character_images)
            pil_images = [Image.open(im) for im in filtered_chararacter_images]

            combined_image = Image.new('RGBA', (5*150-38, 175), (0, 0, 0, 0))
            for index, image in enumerate(pil_images):
                resized_image = image.resize((112, 175))
                resized_image.putalpha(MASK_IMAGE)
                combined_image.paste(resized_image, (150 * index, 0))

            if character is None:
                return

            img_byte_arr = io.BytesIO()
            combined_image.save(img_byte_arr, format='PNG')
            embed.set_thumbnail(character.images[0])
            embed.set_image(img_byte_arr.getvalue())

            embed.add_field(name="⬆️ Upgrade Levels",
                            value=f"Roll Regen Rate: **Lv{upgrades[Upgrades.ROLL_REGEN]}**\nMax Rolls: **Lv{upgrades[Upgrades.ROLL_MAX]}**\nFragment Multiplier: **Lv{upgrades[Upgrades.FRAGMENT_BONUS]}**",
                            inline=True)
            embed.add_field(name="⠀",
                            value=f"Daily Bounty: **Lv{upgrades[Upgrades.DAILY_BONUS]}**\nWishlist Size: **Lv{upgrades[Upgrades.WISHLIST_SIZE]}**\nWishlist Rate: **Lv{upgrades[Upgrades.WISHLIST_RATE_BONUS]}**",
                            inline=True)

            embed.add_field(name="⠀",
                            value=f"**⭐ Display Case**")
        await ctx.respond(embed)
