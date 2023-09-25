import os

import crescent
import hikari

from bot.upgrades import Upgrades
from bot.model import Plugin

plugin = Plugin()

admin_group = crescent.Group("admin")


@plugin.include
@admin_group.child
@crescent.command(
    name="populate",
    description="Add characters to database from file.",
    guild=int(os.environ["GUILD"]),
)
async def populate(ctx: crescent.Context):
    await ctx.respond("`Running command to add characters....`")
    await plugin.model.utils.add_characters_to_db()
    await ctx.respond("`Characters added!`")


@plugin.include
@admin_group.child
@crescent.command(
    name="migratedata",
    description="Migrate data from old scheme to new schema. However, make sure not to run command multiple times for same guild.",
    guild=int(os.environ["GUILD"]),
)
class migratedata:
    guild = crescent.option(
        str,
        "Enter a guild ID to migrate",
        name="guild",
    )

    async def callback(self, ctx: crescent.Context):
        await ctx.respond(f"`Starting migration for guild {self.guild}....`")
        dbsearch = plugin.model.dbsearch
        guild_users = await plugin.model.utils.get_users_from_old_guild_table(self.guild)

        for row in guild_users:
            snowflake = hikari.Snowflake(int(self.guild))

            try:
                discord_userinfo = await plugin.model.bot.rest.fetch_member(snowflake, int(row["id"]))
            except ValueError:
                continue

            user = await dbsearch.create_user(snowflake, discord_userinfo)

            # Set basic info
            await user.set_currency(int(row["currency"]))
            await user.set_claims(int(row["claims"]))
            await user.set_daily_claimed_time(int(row["claimed_daily"]))
            await user.set_rolls(int(row["rolls"]))
            await user.set_rolls_claimed_time(int(row["claimed_rolls"]))

            # Set character list
            for character_id in row["characters"].split(","):
                if character_id == '':
                    continue

                character = await dbsearch.create_character_from_id(
                    snowflake, int(character_id))

                if character is None:
                    continue

                await user.append_to_characters(character)

            # Set wishlist
            for character_id in row["wishlist"].split(","):
                if character_id == '':
                    continue

                character = await dbsearch.create_character_from_id(
                    snowflake, int(character_id))

                if character is None:
                    continue

                await user.append_to_wishlist(character)

            # Set upgrades
            upgrades_list = row["upgrades"].split(",")

            if len(upgrades_list) == 10:
                await user.increase_upgrade_level(Upgrades.ROLL_REGEN, int(upgrades_list[0]))
                await user.increase_upgrade_level(Upgrades.ROLL_MAX, int(upgrades_list[1]))
                await user.increase_upgrade_level(Upgrades.FRAGMENT_BONUS, int(upgrades_list[2]))
                await user.increase_upgrade_level(Upgrades.DAILY_BONUS, int(upgrades_list[3]))
                await user.increase_upgrade_level(Upgrades.WISHLIST_SIZE, int(upgrades_list[4]))
                await user.increase_upgrade_level(Upgrades.WISHLIST_RATE_BONUS, int(upgrades_list[5]))
