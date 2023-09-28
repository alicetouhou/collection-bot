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
            char_info = await self.model.dbpool.fetch(
                "SELECT * FROM characters WHERE ID = $1",
                id,
            )
            series_info = await self.model.dbpool.fetch(
                "SELECT series_id FROM character_series WHERE character_id = $1",
                id,
            )
            images_info = await self.model.dbpool.fetch(
                "SELECT image,index FROM character_images WHERE character_id = $1",
                id,
            )
            character = Character.from_record(
                char_info[0], series=series_info, images=images_info)

            instance = CharacterInstance(guild_id, character, self.model)
            return instance
        except IndexError:
            return None

    async def create_character_from_search(
        self, guild_id: hikari.Snowflake, search: str, limit=20, filter_str=None
    ) -> list[CharacterInstance]:
        search_split = search.split(" ")

        if len(search_split) == 1 and re.match("\d+", search_split[0]):
            id_character = await self.create_character_from_id(guild_id, int(search_split[0]))

            if id_character and (filter_str == None or id_character.id in filter_str):
                return [id_character]
            return []

        searches = ["%" + x + "%" for x in search_split]

        sql = "SELECT * FROM characters "

        for index, s in enumerate(searches):
            sql += f"""AND (
                first_name ILIKE ${index+1}
                OR last_name ILIKE ${index+1} 
                OR id IN (
                    SELECT character_id FROM character_series WHERE series_id IN 
                        (SELECT id FROM series WHERE series_name ILIKE ${index+1})
                    )
                )
                """

        sql = sql.replace("AND", "WHERE", 1)

        if filter_str:
            sql += f""" AND id IN ({','.join([f"'{x}'" for x in filter_str])})"""

        sql += "ORDER BY first_name ILIKE $1 OR NULL, last_name ILIKE $1 OR NULL"

        if limit:
            sql += f" LIMIT {str(limit)}"

        records = await self.model.dbpool.fetch(
            sql,
            *searches,
        )

        output = []
        for record in records:
            series_info = await self.model.dbpool.fetch(
                "SELECT series_id FROM character_series WHERE character_id = $1",
                record["id"],
            )
            output.append(CharacterInstance(
                guild_id, Character.from_record(record, series_info, []), self.model))

        return output

    async def create_random_character(self, context) -> CharacterInstance:
        char_info = await self.model.dbpool.fetch(
            "SELECT * FROM characters ORDER BY RANDOM() LIMIT 1",
        )

        id = char_info[0]["id"]

        series_info = await self.model.dbpool.fetch(
            "SELECT series_id FROM character_series WHERE character_id = $1",
            id,
        )
        images_info = await self.model.dbpool.fetch(
            "SELECT image FROM character_images WHERE character_id = $1",
            id,
        )

        character = Character.from_record(
            char_info[0], series=series_info, images=images_info)
        instance = CharacterInstance(context, character, self.model)
        return instance
