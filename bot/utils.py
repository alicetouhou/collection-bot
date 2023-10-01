import csv
import typing as t

import crescent
import hikari

from bot.character_instance import CharacterInstance
from bot.user import User

if t.TYPE_CHECKING:
    from bot.model import Model


# NOTE: This is used outside this file.
CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE = "You must in a guild to use this command."


async def guild_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if not ctx.guild_id:
        await ctx.respond(CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE)
        return crescent.HookResult(exit=True)
    return None


class Utils:
    """A class containing utility functions for the bot."""

    def __init__(self, model) -> None:
        self.model: Model = model

    async def validate_id_in_list(self, ctx: crescent.Context, user: User, char_id: int) -> CharacterInstance | None:
        if not ctx.guild_id:
            return None

        selected_character = await self.model.dbsearch.create_character_from_id(ctx.guild_id, char_id)

        user_character_ids = await user.characters

        if not selected_character:
            await ctx.respond(f"{char_id} is not a valid ID!")
            return None

        if char_id not in user_character_ids:
            await ctx.respond(
                f"**{selected_character.first_name} {selected_character.last_name}** is not in your list!"
            )
            return None

        return selected_character

    async def validate_search_in_list(self, ctx: crescent.Context, user: User, char_search: str) -> CharacterInstance | None:
        if not ctx.guild_id:
            return None

        selected_character = await self.model.dbsearch.create_character_from_search(ctx.guild_id, char_search)
        user_character_ids = await user.characters

        if len(selected_character) == 0:
            await ctx.respond(f"Your query `{char_search}` did not return any results.")
            return None

        if len(selected_character) > 1:
            await ctx.respond(f"Your query `{char_search}` returned more than one result.")
            return None

        if selected_character[0].id not in user_character_ids:
            await ctx.respond(
                f"**{selected_character[0].first_name} {selected_character[0].last_name}** is not in your list!"
            )
            return None

        return selected_character[0]

    def read_csv_with_header(self, path: str) -> list[list[t.Any]]:
        file = open(path, "r", encoding="utf8")
        character_reader = csv.reader(file, delimiter="|")
        next(character_reader)
        data = []
        for x in character_reader:
            data.append(x)
        return data

    async def add_characters_to_db(self) -> None:
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            characters = self.read_csv_with_header(
                "bot/data/characters.csv")
            series = self.read_csv_with_header("bot/data/series.csv")
            buckets = self.read_csv_with_header(
                "bot/data/buckets.csv")
            character_series = self.read_csv_with_header(
                "bot/data/series_correspondences.csv")
            images_data = self.read_csv_with_header(
                "bot/data/images_correspondences.csv")

            await conn.execute("ALTER TABLE IF EXISTS claimed_characters DROP CONSTRAINT IF EXISTS claimed_characters_character_id_fkey")
            await conn.execute("ALTER TABLE IF EXISTS wishlists DROP CONSTRAINT IF EXISTS wishlists_character_id_fkey")
            await conn.execute("ALTER TABLE IF EXISTS character_series DROP CONSTRAINT IF EXISTS character_series_series_id_fkey")
            await conn.execute("ALTER TABLE IF EXISTS character_images DROP CONSTRAINT IF EXISTS character_images_character_id_fkey")
            await conn.execute("ALTER TABLE IF EXISTS series DROP CONSTRAINT IF EXISTS series_bucket_fkey")

            await conn.execute("DROP TABLE IF EXISTS character_series")
            await conn.execute("DROP TABLE IF EXISTS character_images")
            await conn.execute("DROP TABLE IF EXISTS buckets")
            await conn.execute("DROP TABLE IF EXISTS series")
            await conn.execute("DROP TABLE IF EXISTS characters")

            await conn.execute(
                """CREATE TABLE characters
                (   
                    id int, 
                    first_name varchar(255), 
                    last_name varchar(255), 
                    value int, 
                    PRIMARY KEY (id)
                )
                """
            )

            await conn.execute(
                """CREATE TABLE buckets
                (   
                    id int,
                    name varchar(255),
                    PRIMARY KEY (id)
                )
                """
            )

            await conn.execute(
                """CREATE TABLE series
                (   
                    id int,
                    name varchar(255), 
                    type varchar(15),
                    bucket int references buckets(id),
                    PRIMARY KEY (id)
                )
                """
            )

            await conn.execute(
                """CREATE TABLE character_series
                (   
                    character_id int references characters(id),
                    series_id int references series(id),
                    PRIMARY KEY (character_id,series_id)
                )
                """
            )

            await conn.execute(
                """CREATE TABLE character_images
                (   
                    character_id int references characters(id),
                    image varchar(255),
                    index int,
                    PRIMARY KEY (character_id,image)
                )
                """
            )

            await conn.executemany(
                """
                INSERT INTO characters 
                (id, first_name, last_name, value) 
                VALUES ($1, $2, $3, $4)""",
                [[int(x[0]), x[1], x[2], int(x[3])] for x in characters],
            )

            await conn.executemany(
                """
                INSERT INTO buckets 
                (id, name) 
                VALUES ($1, $2) 
                ON CONFLICT DO NOTHING""",
                [[int(x[0]), x[1]] for x in buckets],
            )

            await conn.executemany(
                """
                INSERT INTO series 
                (id, name, type, bucket) 
                VALUES ($1, $2, $3, $4) 
                ON CONFLICT DO NOTHING""",
                [[int(x[0]), x[1], x[2], int(x[3])] if int(x[3]) > 0 else [
                    int(x[0]), x[1], x[2], None] for x in series],
            )

            await conn.executemany(
                """
                INSERT INTO character_series 
                (character_id, series_id) 
                VALUES ($1, $2) 
                ON CONFLICT DO NOTHING""",
                [[int(x[0]), int(x[1])] for x in character_series],
            )

            await conn.executemany(
                """
                INSERT INTO character_images 
                (character_id, image, index) 
                VALUES ($1, $2, $3) 
                ON CONFLICT DO NOTHING""",
                [[int(x[0]), x[1], i] for i, x in enumerate(images_data)],
            )

            await conn.execute("ALTER TABLE claimed_characters ADD FOREIGN KEY (character_id) REFERENCES characters(id)")
            await conn.execute("ALTER TABLE wishlists ADD FOREIGN KEY (character_id) REFERENCES characters(id)")

    async def save_correspondences(self):
        pass

    async def character_search_autocomplete(
        self, ctx: crescent.AutocompleteContext, include_series=False
    ) -> list[tuple[str, str]]:
        options = ctx.options

        if len(options["search"]) == 0:
            return []

        if not ctx.guild_id:
            return []

        character_list = await self.model.dbsearch.create_character_from_search(ctx.guild_id, options["search"])

        output = []
        for character in character_list:
            name = f"{character.first_name} {character.last_name} ({character.get_top_series()['name']})"
            if len(name) > 100:
                name = name[0:98] + "..."
            output.append((name, str(character.id)))

        if include_series == True:
            series_list = await self.model.dbsearch.get_series_from_search(options["search"])
            for s in series_list:
                output.insert(0, (s, s))
        return output

    async def character_search_in_list_autocomplete(
        self, ctx: crescent.AutocompleteContext, option: str = "search", char_filter=None,
    ) -> list[tuple[str, str]]:
        if not ctx.guild_id:
            return []

        options = ctx.options
        user = await self.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        if char_filter is None:
            char_filter = await user.characters
        character_list = await self.model.dbsearch.create_character_from_search(
            ctx.guild_id,
            options[option],
            filter_str=char_filter
        )

        output = []
        for character in character_list:
            name = f"{character.first_name} {character.last_name} ({character.get_top_series()['name']})"
            if len(name) > 100:
                name = name[0:98] + "..."
            output.append((name, str(character.id)))
        return output

    async def get_users_from_old_guild_table(self, guild: str):
        records = await self.model.dbpool.fetch(
            f"SELECT * FROM players_{guild}"
        )
        return records

    async def get_series(self):
        records = await self.model.dbpool.fetch(
            f"SELECT * FROM series"
        )
        return records

    async def get_characters(self):
        records = await self.model.dbpool.fetch(
            f"SELECT * FROM characters"
        )
        return records

    async def get_series_id_from_name(self, name: str, type: str):
        records = await self.model.dbpool.fetch(
            f"SELECT id FROM series WHERE series_name = $1 AND type = $2",
            name,
            type
        )
        return records[0]
