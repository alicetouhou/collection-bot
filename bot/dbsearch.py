from __future__ import annotations
import typing as t
import asyncpg
from bot.character import Character
from bot.character_instance import CharacterInstance
from bot.user import User

import hikari
import re

if t.TYPE_CHECKING:
    from bot.model import Model


class DBSearch:
    def __init__(self, model: "Model"):
        self.model = model

    async def create_user(self, guild_id: hikari.Snowflake, player_id: hikari.User) -> User:
        user = User(guild_id, player_id, self.model)
        await user.add_player_to_db()
        return user

    async def create_character(self, guild_id: hikari.Snowflake, character: Character) -> CharacterInstance:
        instance = CharacterInstance(guild_id, character, self.model)
        return instance

    async def create_character_from_id(self, guild_id: hikari.Snowflake, id: int) -> CharacterInstance | None:
        """Returns `Character` if one exists with the ID. Otherwise, `None` is returned."""
        try:
            records = await self.model.dbpool.fetch(
                """SELECT characters.*, character_series.*, series.name AS series_name, series.type AS type, 
                buckets.name AS bucket_name, character_images.image, character_images.index AS image_index
                FROM characters
                LEFT JOIN character_series ON characters.id = character_series.character_id
                LEFT JOIN character_images ON characters.id = character_images.character_id
                LEFT JOIN series ON character_series.series_id = series.id
                LEFT JOIN buckets ON series.bucket = buckets.id
                WHERE characters.id = $1""",
                id
            )

            character = Character.from_record(
                await self.create_combined_record(records))
            instance = CharacterInstance(guild_id, character, self.model)
            return instance
        except IndexError:
            return None

    async def create_characters_from_ids(self, guild_id: hikari.Snowflake, ids: list[int], order_by=None) -> list[CharacterInstance]:
        """Returns `list[Character]` for the IDs inputted. Only the name, id, and value are available."""

        sql = f"""SELECT * FROM characters
            JOIN claimed_characters ON claimed_characters.character_id = characters.id
            WHERE id IN ({','.join([f"'{x}'" for x in ids])})
            """

        if order_by == "value":
            sql += "ORDER BY characters.value DESC"
        else:
            sql += "ORDER BY claimed_characters.list_order"

        try:
            records = await self.model.dbpool.fetch(sql)

            output = []
            for record in records:
                character = Character.from_record(
                    await self.create_combined_record([record]))
                instance = CharacterInstance(guild_id, character, self.model)
                output.append(instance)
            return output
        except IndexError:
            return []

    async def create_combined_record(self, records: list[asyncpg.Record]) -> dict[str, t.Any]:
        images: list[dict[str, str | int]] = []
        series: list[dict[str, t.Any]] = []

        for r in records:
            if "image" in r:
                images_entry = {"image": r["image"],
                                "image_index": r["image_index"]
                                }
                if images_entry not in images:
                    images.append(images_entry)
            if "series_name" in r:
                series_entry = {"name": r["series_name"], "type": r["type"]}
                if series_entry not in series:
                    series.append(series_entry)

        combined_record: asyncpg.Record = {
            "id": records[0]["id"],
            "first_name": records[0]["first_name"],
            "last_name": records[0]["last_name"],
            "value": records[0]["value"],
            "images": images,
            "series": series,
            "bucket": {"name": records[0]["bucket_name"], "type": "bucket"} if "bucket_name" in records[0] and records[0]["bucket_name"] else None
        }

        return combined_record

    async def create_character_from_search(
        self, guild_id: hikari.Snowflake, search: str, limit=100, filter_str=None, order_by=None
    ) -> list[CharacterInstance]:
        search_split = search.split(" ")

        if len(search_split) == 1 and re.match("\d+", search_split[0]):
            id_character = await self.create_character_from_id(guild_id, int(search_split[0]))

            if id_character and (filter_str == None or id_character.id in filter_str):
                return [id_character]
            return []

        searches = ["%" + x + "%" for x in search_split]

        sql = """SELECT characters.*, character_series.*, series.name AS series_name, series.type AS type, buckets.name AS bucket_name
            FROM characters
            LEFT JOIN character_series ON characters.id = character_series.character_id
            LEFT JOIN series ON character_series.series_id = series.id
            LEFT JOIN buckets ON series.bucket = buckets.id """

        for index, s in enumerate(searches):
            sql += f"""AND (
                first_name ILIKE ${index+1}
                OR last_name ILIKE ${index+1} 
                OR series.name ILIKE ${index+1}
                OR buckets.name ILIKE ${index+1}
                )
                """

        sql = sql.replace("AND", "WHERE", 1)

        if filter_str:
            sql += f""" AND characters.id IN ({','.join([f"'{x}'" for x in filter_str])})"""

        if order_by == "value":
            sql += "ORDER BY value"
        else:
            sql += "ORDER BY first_name ILIKE $1 OR NULL, last_name ILIKE $1 OR NULL"

        if limit:
            sql += f" LIMIT {str(limit)}"

        records = await self.model.dbpool.fetch(
            sql,
            *searches,
        )

        output: list[CharacterInstance] = []
        for record in records:
            if len(output) >= 20:
                break
            if record["character_id"] not in [x.id for x in output]:
                output.append(CharacterInstance(
                    guild_id, Character.from_record(await self.create_combined_record([record])), self.model))

        return output

    async def create_random_character(self, context) -> CharacterInstance:
        records = await self.model.dbpool.fetch(
            """SELECT characters.*, character_series.*, series.name AS series_name, series.type AS type, 
            buckets.name AS bucket_name, character_images.image, character_images.index AS image_index
            FROM characters
            LEFT JOIN character_series ON characters.id = character_series.character_id
            LEFT JOIN character_images ON characters.id = character_images.character_id
            LEFT JOIN series ON character_series.series_id = series.id
            LEFT JOIN buckets ON series.bucket = buckets.id
            WHERE characters.id = (SELECT id FROM characters ORDER BY RANDOM() LIMIT 1)""",
        )

        character = Character.from_record(
            await self.create_combined_record(records))
        instance = CharacterInstance(context, character, self.model)
        return instance

    async def get_series_from_search(self, search: str) -> list[str]:

        search = f"%{search}%"

        records = await self.model.dbpool.fetch(
            """
            SELECT * FROM
                (SELECT name FROM series WHERE name ILIKE $1
                UNION
                SELECT name FROM buckets WHERE name ILIKE $1) AS seriesandbucketstable
            ORDER BY name ILIKE $1 LIMIT 5
            """,
            search
        )

        output = []
        for record in records:
            output.append(record["name"])

        return output
