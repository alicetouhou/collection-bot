import csv
import typing as t

from bot.character import Character

import crescent
import hikari

if t.TYPE_CHECKING:
    from bot.model import Model

class User:
    """A class that handles all DB functions for the player"""

    guild: hikari.Snowflake = None
    player_id: hikari.Snowflake = None
    name: str = None

    _guild_str: str = None

    _characters: list[str] = None
    _wishlist: list[str] = None

    _currency: int = None
    _rolls: int = None
    _claims: int = None

    _rolls_claimed_time: str = None
    _daily_claimed_time: str = None

    def __init__(self, ctx: crescent.Context, user: hikari.User, model):
        self.guild = hikari.Snowflake(ctx.guild_id)
        self.player_id = user.id
        self._guild_str = f"players_{hikari.Snowflake(ctx.guild_id)}"
        self.name = user.username
        self.model = model

    async def add_player_to_db(self):
        await self.model.dbpool.execute(
            f"INSERT INTO {self._guild_str} VALUES ($1,'',$2,3,0,10,0,'','') ON CONFLICT DO NOTHING",
            str(self.player_id),
            0,
        )

    async def _fetch(self, param: any, field: str):
        if param is None:
            records = await self.model.dbpool.fetch(f"SELECT {field} FROM {self._guild_str} WHERE ID = $1", str(self.player_id))
            return records[0][field]
        return param
    
    async def _execute(self, value: any, field: str):
        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                value,
                str(self.player_id),
            )
        return value

    @property
    async def rolls(self) -> int:
        return await self._fetch(self._rolls, "rolls")

    async def set_rolls(self, value: int) -> None:
        await self._execute(value, "rolls")
        self._rolls = value
        if (self._rolls):
            self._rolls = value

    @property 
    async def rolls_claimed_time(self) -> int:
        return await self._fetch(self._rolls_claimed_time, "claimed_rolls")

    async def set_rolls_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_rolls")
        self._rolls_claimed_time = value
        if (self._rolls_claimed_time):
            self._rolls_claimed_time = value

    @property 
    async def claims(self) -> int:
        return await self._fetch(self._claims, "claims")

    async def set_claims(self, value: int) -> None:
        await self._execute(value, "claims")
        if (self._claims):
            self._claims = value

    @property 
    async def daily_claimed_time(self) -> int:
        return await self._fetch(self._daily_claimed_time, "claimed_daily")

    async def set_daily_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_daily")
        if (self._daily_claimed_time):
            self._daily_claimed_time = value

    @property 
    async def currency(self) -> int:
        return await self._fetch(self._currency, "currency")

    async def set_currency(self, value: int) -> None:
        await self._execute(value, "currency")
        if (self._currency):
            self._currency = value

    async def _fetch_character_group(self, param: any, field: str) -> list[int]:
        if param is None:
            record = await self.model.dbpool.fetch(f"SELECT {field} FROM {self._guild_str} WHERE ID = $1", str(self.player_id))
            character_str = record[0][field]
            character_ids_list = character_str.split(",")
            filtered_list = filter(lambda x: x != '', character_ids_list)
            return [int(x) for x in filtered_list]
        return param
    
    async def _append_to_chararacter_list(self, list, character: Character, field: str, prepend=False):
        async with self.model.dbpool.acquire() as conn:
            if prepend is False:
                list.append(character.id)
            else:
                list = [character.id] + list

            stringified_list = ",".join(map(str, list))

            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                stringified_list,
                str(self.player_id),
            )

    async def _remove_from_character_list(self, list, character: Character, field: str):
        async with self.model.dbpool.acquire() as conn:
            list.remove(character.id)
            
            stringified_list = ",".join(map(str, list))

            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                stringified_list,
                str(self.player_id),
            )

    @property
    async def characters(self) -> int:
        return await self._fetch_character_group(self._characters, "characters")
    
    async def append_to_characters(self, character: Character, prepend=False):
        self._characters = await self._fetch_character_group(self._characters, "characters")
        await self._append_to_chararacter_list(self._characters, character, "characters", prepend=prepend)
        self._characters = await self._fetch_character_group(self._characters, "characters")

    async def remove_from_characters(self, character: Character):
        self._characters = await self._fetch_character_group(self._characters, "characters")
        await self._remove_from_character_list(self._characters, character, "characters")
        self._characters = await self._fetch_character_group(self._characters, "characters")
    
    @property
    async def wishlist(self) -> int:
        return await self._fetch_character_group(self._wishlist, "wishlist")
    
    async def append_to_wishlist(self, character: Character):
        self._wishlist = await self._fetch_character_group(self._wishlist, "wishlist")
        await self._append_to_chararacter_list(self._wishlist, character, "wishlist")
        self._wishlist = await self._fetch_character_group(self._wishlist, "wishlist")

    async def remove_from_wishlist(self, character: Character):
        self._wishlist = await self._fetch_character_group(self._wishlist, "wishlist")
        await self._remove_from_character_list(self._wishlist, character, "wishlist")
        self._wishlist = await self._fetch_character_group(self._wishlist, "wishlist")

    async def reorder(self, character: Character):
        await self.remove_from_characters(character)
        await self.append_to_characters(character, prepend=True)