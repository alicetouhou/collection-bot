import csv
import typing as t

import crescent
import hikari

from bot.character import Character

if t.TYPE_CHECKING:
    from bot.model import Model


Plugin = crescent.Plugin[hikari.GatewayBot, Model]
"""Type alias for the plugin type used by the bot."""


class Utils:
    """A class containing utility functions for the bot."""

    def __init__(self, model: Model) -> None:
        self.model = model

    async def add_player_to_db(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int):
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.model.dbpool.execute(
            f"INSERT INTO {guild_str} VALUES ($1,'',$2,3,0,10,0,'','') ON CONFLICT DO NOTHING",
            guild_str,
            str(id),
            0,
        )

    async def pick_random_character(self) -> Character:
        records = await self.model.dbpool.fetch(
            "SELECT * FROM characters ORDER BY RANDOM() LIMIT 1",
        )
        return Character.from_record(records[0])

    async def claim_character(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, character: Character, prepend=False
    ) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT characters FROM {guild_str} WHERE ID = $1", str(id))
            old_list = records[0]["characters"]
            if old_list is not None:
                if prepend is False:
                    new_list = old_list + "," + str(character.id)
                else:
                    new_list = str(character.id) + "," + old_list
                await conn.execute(
                    "UPDATE $1 SET characters = $2 WHERE ID = $3",
                    guild_str,
                    new_list,
                    id,
                )

    async def remove_character(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, character: Character
    ) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT characters FROM {guild_str} WHERE ID = $1", str(id))
            old_list = records[0]["characters"]
            if old_list is not None:
                new_list = old_list.split(",")
                new_list.remove(str(character.id))
                new_list = ",".join(new_list)
                await conn.execute(
                    f"UPDATE {guild_str} SET characters = $1 WHERE ID = $2",
                    new_list,
                    id,
                )

    async def get_characters(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> list[Character]:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT characters FROM {guild_str} WHERE ID = $1", str(id))
            character_str = records[0]["characters"]
            character_ids_list = character_str.split(",")
            character_list = []
            for char_id in character_ids_list:
                if char_id != "":
                    records = await conn.fetch("SELECT * FROM characters WHERE ID = $1", int(char_id))
                    character_list.append(Character.from_record(records[0]))
            return character_list

    async def reorder(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, character: Character):
        await self.remove_character(guild, id, character)
        await self.claim_character(guild, id, character, prepend=True)

    async def add_wish(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, character: Character) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT wishlist FROM {guild_str} WHERE ID = $1", str(id))
            old_list = records[0]["wishlist"]
            if old_list is not None:
                new_list = old_list + "," + str(character.id)
                await conn.execute(
                    f"UPDATE {guild_str} SET wishlist = $2 WHERE ID = $3",
                    new_list,
                    id,
                )

    async def remove_wish(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, character: Character
    ) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT wishlist FROM {guild_str} WHERE ID = $1", str(id))
            old_list = records[0]["wishlist"]
            if old_list is not None:
                new_list = old_list.split(",")
                new_list.remove(str(character.id))
                new_list = ",".join(new_list)
                await conn.execute(
                    f"UPDATE {guild_str} SET wishlist = $1 WHERE ID = $2",
                    new_list,
                    id,
                )

    async def get_wishes(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> list[Character]:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT wishlist FROM {guild_str} WHERE ID = $1", str(id))
            character_str = records[0]["wishlist"]
            character_ids_list = character_str.split(",")
            character_list = []
            for char_id in character_ids_list:
                if char_id != "":
                    records = await conn.fetch("SELECT * FROM characters WHERE ID = $1", int(char_id))
                    character_list.append(Character.from_record(records[0]))
            return character_list

    async def get_users_who_wished(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], character: Character
    ) -> list[int]:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        records = await self.model.dbpool.fetch(f"SELECT id, wishlist FROM {guild_str}")
        users = []
        for record in records:
            if str(character.id) in record["wishlist"]:
                users.append(record["id"])
        return users

    async def is_claimed(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], character: Character) -> bool:
        guild_str = f"players_{hikari.Snowflake(guild)}"

        records = await self.model.dbpool.fetch(f"SELECT characters FROM {guild_str}")
        for record in records:
            if str(character.id) in record["characters"]:
                return True
        return False

    async def get_daily_claimed_time(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> int:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        records = await self.model.dbpool.fetch(f"SELECT claimed_daily FROM {guild_str} WHERE ID = $1", str(id))
        return records[0]["claimed_daily"]

    async def set_daily_claimed_time(
        self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, time: int
    ) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)
        await self.model.dbpool.execute(
            f"UPDATE {guild_str} SET claimed_daily = $2 WHERE ID = $3",
            time,
            id,
        )

    async def get_claims(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> int:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)
        records = await self.model.dbpool.fetch(f"SELECT claims FROM {guild_str} WHERE ID = $2", str(id))
        return records[0]["claims"]

    async def add_claims(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, number: int) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)
        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT claims FROM {guild_str} WHERE ID = $2", str(id))
            old_amount = records[0]["claims"]
            if old_amount is not None:
                new_amount = old_amount + number
                await conn.execute(
                    f"UPDATE {guild_str} SET claims = $2 WHERE ID = $3",
                    new_amount,
                    id,
                )

    async def get_daily_rolls_time(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> int:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        records = await self.model.dbpool.fetch(f"SELECT claimed_rolls FROM {guild_str} WHERE ID = $2", str(id))
        return records[0]["claimed_rolls"]

    async def set_daily_rolls_time(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, time: int) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        await self.model.dbpool.execute(
            f"UPDATE {guild_str} SET claimed_rolls = $1 WHERE ID = $2",
            time,
            id,
        )

    async def get_rolls(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> int:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        records = await self.model.dbpool.fetch(f"SELECT rolls FROM {guild_str} WHERE ID = $2", str(id))
        return records[0]["rolls"]

    async def add_rolls(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, number: int) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT rolls FROM {guild_str} WHERE ID = $2", str(id))
            old_amount = records[0]["rolls"]
            if old_amount is not None:
                new_amount = old_amount + number
                await conn.execute(
                    f"UPDATE {guild_str} SET rolls = $2 WHERE ID = $3",
                    new_amount,
                    id,
                )

    async def get_currency(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int) -> int:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        records = await self.model.dbpool.fetch(f"SELECT currency FROM {guild_str} WHERE ID = $1", str(id))
        return records[0]["currency"]

    async def add_currency(self, guild: hikari.SnowflakeishOr[hikari.PartialGuild], id: int, number: int) -> None:
        guild_str = f"players_{hikari.Snowflake(guild)}"
        await self.add_player_to_db(guild, id)

        async with self.model.dbpool.acquire() as conn:
            records = await conn.fetch(f"SELECT currency FROM {guild_str} WHERE ID = $1", str(id))
            old_amount = records[0]["currency"]
            if old_amount is not None:
                new_amount = old_amount + number
                await conn.execute(
                    f"UPDATE {guild_str} SET currency = $1 WHERE ID = $2",
                    new_amount,
                    id,
                )

    # TODO: Fix me
    async def search_characters(
        self,
        id: int | None,
        name: str | None,
        appearances: str | None,
        limit: int = 0,
        fuzzy: bool = False,
    ) -> list[Character]:
        async with self.model.dbpool.acquire() as conn:
            first_name = None
            last_name = None
            if name:
                first_name = name
                last_name = None
                names = name.split(" ")
                if len(names) > 1:
                    first_name = " ".join(names[0 : len(names) - 1])
                    last_name = names[len(names) - 1]

            sql = "SELECT * FROM characters "

            if id:
                sql += f"AND ID = {id} "
            if first_name:
                sql += f"AND LOWER(first_name) = LOWER({first_name}) "
            if last_name:
                sql += f"AND LOWER(last_name) = LOWER({last_name}) "

            if fuzzy is True:
                first_name = "%" + first_name + "%" if first_name else None
                last_name = "%" + last_name + "%" if last_name else None
                sql = sql[::-1].replace("=", "EKIL", 2)[::-1]

            if appearances:
                appearances = "%" + appearances + "%"
                sql += f"AND (LOWER(anime_list) LIKE LOWER({appearances}) OR LOWER(manga_list) LIKE LOWER({appearances}) OR LOWER(games_list) LIKE LOWER({appearances})"
            sql += "ORDER BY first_name "
            sql = sql.replace("AND", "WHERE", 1)
            if limit > 0:
                sql += f"LIMIT {limit}"

            characters_a = await conn.fetch(sql)

            characters_b = []
            if first_name is not None:
                sql = sql.replace("first_name", "temp_name")
                sql = sql.replace("last_name", "first_name")
                sql = sql.replace("temp_name", "last_name")
                characters_b = await conn.fetch(
                    sql,
                    {
                        "id": id,
                        "first_name": last_name,
                        "last_name": first_name,
                        "appearences": appearances,
                    },
                )

            character_list = []
            for record in characters_a:
                character_list.append(Character.from_record(record))
            for record in characters_b:
                character_list.append(Character.from_record(record))

            return character_list

    async def add_characters_to_db(self) -> None:
        async with self.model.dbpool.acquire() as conn:
            f = open("bot/data/db.csv", "r")
            reader = csv.reader(f, delimiter="|")
            tuples = [tuple(x) for x in reader]

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
                tuples,
            )
