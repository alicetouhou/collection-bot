import crescent
import hikari
import io
import aiohttp
import asyncio

from PIL import Image

from bot.upgrades import Upgrades
from bot.model import Plugin
from bot.character_instance import CharacterInstance

plugin = Plugin()
MASK_IMAGE = Image.open('bot/data/mask.png').convert('L')


async def open_image_from_characters(ctx: crescent.Context, characters: list[CharacterInstance]) -> list[io.BytesIO]:
    if not ctx.guild_id:
        return []

    image_list = []
    for character in characters:
        default_image = await character.get_default_image()

        if default_image is None:
            continue

        image_url = character.images[default_image]
        async with aiohttp.ClientSession() as session:
            async with session.get(url=image_url) as response:
                resp = await response.read()
                image = io.BytesIO(resp)
                image_list.append(image)
    return image_list


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

            first_character = await dbsearch.create_character_from_id(ctx.guild_id, character_list[0])

            if first_character is None:
                return

            default_image = await first_character.get_default_image()
            if default_image:
                first_image = first_character.images[default_image]
            else:
                first_image = first_character.images[0]

            description = f'💛 Top character: **{first_character.first_name} {first_character.last_name}**\n📚 List size: **{len(character_list)}**' + \
                description
        embed = hikari.embeds.Embed(
            title=f"{user.name}'s Stats", color="f598df", description=description)
        if character_list:
            top_characters = await dbsearch.create_characters_from_ids(
                ctx.guild_id, character_list[:10])
            character_images = await open_image_from_characters(
                ctx, top_characters)

            pil_images = [Image.open(im) for im in character_images]

            combined_image = Image.new('RGBA', (5*150-38, 388), (0, 0, 0, 0))
            for index, image in enumerate(pil_images):
                resized_image = image.resize((112, 175))
                resized_image.putalpha(MASK_IMAGE)
                combined_image.paste(
                    resized_image, ((150 * index) % 750, int(index/5) * 213)
                )

            if first_character is None:
                return

            img_byte_arr = io.BytesIO()
            combined_image.save(img_byte_arr, format='PNG')

            embed.set_thumbnail(first_image)
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
