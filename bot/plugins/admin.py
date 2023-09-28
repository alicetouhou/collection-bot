import os

import crescent
import hikari
import csv

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
    name="savecorrespondences",
    description="Add corrospondences to CSV from database.",
    guild=int(os.environ["GUILD"]),
)
async def save_correspondences(ctx: crescent.Context):
    await ctx.respond("`Running command to save correspondences....`")
    file = open("bot\data\series_correspondences.csv",
                "w", newline="", encoding="utf8")

    character_file = open("bot/data/db.csv", "r", encoding="utf8")
    reader = csv.reader(character_file, delimiter="|")
    next(reader)
    data = []
    series_correspondences: list[list[int]] = []
    for x in reader:
        try:
            data.append([x[0], x[3], x[6], x[7]])

        except IndexError:
            print(f"Error adding: {x}")

    for row in data:
        for series in row[1].split(","):
            if series == '':
                continue
            series_id = await plugin.model.utils.get_series_id_from_name(series, "anime")
            series_correspondences.append([int(row[0]), series_id["id"]])
        for series in row[2].split(","):
            if series == '':
                continue
            series_id = await plugin.model.utils.get_series_id_from_name(series, "manga")
            series_correspondences.append([int(row[0]), series_id["id"]])
        for series in row[3].split(","):
            if series == '':
                continue
            series_id = await plugin.model.utils.get_series_id_from_name(series, "game")
            series_correspondences.append([int(row[0]), series_id["id"]])

    writer = csv.writer(file, delimiter="|")
    writer.writerow(("character_id", "series_id"))
    writer.writerows([[x[0], x[1]] for x in series_correspondences])
    await ctx.respond("`Complete!`")

# @plugin.include
# @admin_group.child
# @crescent.command(
#     name="savebuckets",
#     description="Add series buckets automatically. Mistakes will probably be made.",
#     guild=int(os.environ["GUILD"]),
# )
# async def save_buckets(ctx: crescent.Context):
#     await ctx.respond("`Running command to save buckets....`")
#     file = open("bot\data\series.csv",
#                 "r+", newline="", encoding="utf8")

#     reader = csv.reader(file, delimiter="|")
#     next(reader)
#     series_list = []
#     buckets: dict[int, dict[str, str | list[int]]] = {}
#     for x in reader:
#         try:
#             series_list.append([x[0], x[1], x[2]])

#         except IndexError:
#             print(f"Error adding: {x}")

#     current_name = ""
#     current_id = 200000
#     for row in series_list:
#         if current_name == "" or current_name not in row[1]:
#             current_name = row[1]
#             buckets[current_id] = {
#                 "name": row[1],
#                 "series": []
#             }
#             current_id += 1
#         buckets[current_id-1]["series"].append(int(row[0]))

#     new_file = open("bot\data\\bucket_correspondences.csv",
#                     "w", newline="", encoding="utf8")

#     buckets_list = []
#     buckets_name = []
#     for key in buckets:
#         if len(buckets[key]["series"]) == 1:
#             continue
#         buckets_name.append([key, buckets[key]["name"], "bucket"])
#         for item in buckets[key]["series"]:
#             buckets_list.append([str(key), str(item)])

#     writer = csv.writer(new_file, delimiter="|")
#     writer.writerow(("bucket_id", "series_id"))
#     writer.writerows(buckets_list)

#     original_writer = csv.writer(file, delimiter="|")
#     original_writer.writerows(buckets_name)
#     await ctx.respond("`Complete!`")


@plugin.include
@admin_group.child
@crescent.command(
    name="migratedata",
    description="Migrate data from old scheme to new schema. Do not run multiple times for same guild.",
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

        await ctx.respond(f"`Completed migration for guild {self.guild}!`")
