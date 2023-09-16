import csv
import typing as t

from bot.character import Character
from bot.character_instance import CharacterInstance
from bot.user import User

import crescent
import miru
import hikari
import re

if t.TYPE_CHECKING:
    from bot.model import Model


class DBSearch:

    def __init__(self, model):
        self.model = model

    async def create_user(self, context: crescent.Context | crescent.AutocompleteContext | miru.ViewContext, player_id) -> User:
        user = User(context, player_id, self.model)
        await user.add_player_to_db()
        return user

    async def create_character(self, context: crescent.Context, character: Character) -> CharacterInstance:
        instance = CharacterInstance(context, character, self.model)
        return instance

    async def create_character_from_id(self, context: crescent.Context, id: int) -> CharacterInstance | None:
        """Returns `Character` if one exists with the ID. Otherwise, `None` is returned."""
        try:
            records = await self.model.dbpool.fetch(
                "SELECT * FROM characters WHERE ID = $1", id,
            )
            character = Character.from_record(records[0])
            instance = CharacterInstance(context, character, self.model)
            return instance
        except IndexError:
            return None

    async def create_character_from_search(self, ctx, search: str, limit=20, filter=None) -> list[CharacterInstance]:
        search_split = search.split(" ")

        if len(search_split) == 1 and re.match("\d+", search_split[0]):
            id_character = await self.create_character_from_id(ctx, int(search_split[0]))

            if id_character and (filter == None or id_character.id in filter):
                return [id_character]
            return []

        sql = "SELECT * FROM characters "

        for index, search in enumerate(search_split):
            sql += f"""AND (
                LOWER(first_name) LIKE LOWER(${index+1}) 
                OR LOWER(last_name) LIKE LOWER(${index+1}) 
                OR LOWER(anime_list) LIKE LOWER(${index+1}) 
                OR LOWER(manga_list) LIKE LOWER(${index+1}) 
                OR LOWER(games_list) LIKE LOWER(${index+1})) 
                """.replace("\n", "").replace("                ", "")

        sql = sql.replace("AND", "WHERE", 1)

        if filter:
            sql += f""" AND id IN ({','.join([f"'{x}'" for x in filter])})"""

        sql += "ORDER BY LOWER(first_name) ILIKE $1 OR NULL, LOWER(last_name) ILIKE $1 OR NULL, LOWER(anime_list) ILIKE $1 OR NULL, LOWER(manga_list) ILIKE $1 OR NULL, LOWER(games_list) ILIKE $1 OR NULL"

        if limit:
            sql += f" LIMIT {str(limit)}"

        searches = ["%" + x + "%" for x in search_split]

        records = await self.model.dbpool.fetch(
            sql, *searches,
        )

        output = []
        for record in records:
            output.append(CharacterInstance(
                ctx, Character.from_record(record), self.model))

        return output

    async def create_random_character(self, context) -> CharacterInstance:
        records = await self.model.dbpool.fetch(
            "SELECT * FROM characters ORDER BY RANDOM() LIMIT 1",
        )
        character = Character.from_record(records[0])
        instance = CharacterInstance(context, character, self.model)
        return instance
