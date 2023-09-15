import csv
import typing as t

import crescent
import hikari

from bot.character import Character
from bot.user import User

if t.TYPE_CHECKING:
    from bot.model import Model


class Utils:
    """A class containing utility functions for the bot."""

    def __init__(self, model) -> None:
        self.model: Model = model

    async def validate_id_in_list(self, ctx: crescent.Context, user: User, char_id: int) -> Character | None:
        selected_character = await self.model.dbsearch.create_character_from_id(ctx, char_id)

        user_character_ids = await user.characters

        if not selected_character:
            await ctx.respond(f"{char_id} is not a valid ID!")
            return None

        character = selected_character.character

        if char_id not in user_character_ids:
            await ctx.respond(f"**{character.first_name} {character.last_name}** is not in your list!")
            return None

        return character

    async def search_characters(
        self,
        id: int | None,
        name: str | None,
        appearances: str | None,
        limit: int = 0,
        fuzzy: bool = False,
    ) -> list[Character]:
        if self.model.dbpool is None:
            return []

        async with self.model.dbpool.acquire() as conn:
            fn = None
            ln = None
            if name:
                fn = name
                ln = None
                names = name.split(" ")
                if len(names) > 1:
                    fn = " ".join(names[0: len(names) - 1])
                    ln = names[len(names) - 1]

            sql = "SELECT * FROM characters "
            args = []

            if id:
                sql += f"AND ID = $1 "
                args.append(str(id))
            if fn:
                sql += f"AND LOWER(first_name) = LOWER($2) "
                fn = "%" + fn + "%" if fuzzy else fn
                args.append(fn)
            if ln:
                sql += f"AND LOWER(last_name) = LOWER($3) "
                ln = "%" + ln + "%" if fuzzy else ln
                args.append(ln)

            if fuzzy is True:
                sql = sql[::-1].replace("=", "EKIL", 2)[::-1]

            if appearances:
                appearances = "%" + appearances + "%"
                sql += f"AND (LOWER(anime_list) LIKE LOWER($4) OR LOWER(manga_list) LIKE LOWER($4) OR LOWER(games_list) LIKE LOWER($4)) "
                args.append(str(appearances))
            sql += "ORDER BY first_name "
            sql = sql.replace("AND", "WHERE", 1)
            if limit > 0:
                sql += f"LIMIT {limit}"

            if "$3" not in sql:
                sql = sql.replace("$4", "$3")
            if "$2" not in sql:
                sql = sql.replace("$3", "$2")
            if "$1" not in sql:
                sql = sql.replace("$2", "$1")
            if "$2" not in sql:
                sql = sql.replace("$3", "$2")

            characters_a = await conn.fetch(sql, *args)

            characters_b = []

            sql = sql.replace("first_name", "temp_name")
            sql = sql.replace("last_name", "first_name")
            sql = sql.replace("temp_name", "last_name")

            characters_b = await conn.fetch(sql, *args)

            character_list = []
            for record in characters_a:
                if record not in character_list:
                    character_list.append(Character.from_record(record))
            for record in characters_b:
                if record not in character_list:
                    character_list.append(Character.from_record(record))

            return character_list

    async def add_characters_to_db(self) -> None:
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            f = open("bot/data/db.csv", "r", encoding="utf8")
            reader = csv.reader(f, delimiter="|")
            next(reader)
            data = []
            for x in reader:
                data.append([int(x[0]), x[1], x[2], x[3],
                            x[4], int(x[5]), x[6], x[7]])

            await conn.execute("DROP TABLE IF EXISTS characters")
            await conn.execute(
                """CREATE TABLE characters
                (   
                    ID int, 
                    first_name varchar(255), 
                    last_name varchar(255), 
                    anime_list varchar(1027), 
                    pictures varchar(2055), 
                    value int, 
                    manga_list varchar(1027), 
                    games_list varchar(1027), 
                    PRIMARY KEY (ID)
                )
                """
            )

            await conn.executemany(
                """
                INSERT INTO characters 
                (ID, first_name, last_name, anime_list, pictures, value, manga_list, games_list) 
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)""",
                data,
            )
