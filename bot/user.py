import typing as t

from bot.character import Character
from bot import shop_item as items
from bot.upgrades import Upgrades, UpgradeEffects

import hikari

if t.TYPE_CHECKING:
    from bot.model import Model


class User:
    """A class that handles all DB functions for the player"""

    guild: hikari.Snowflake | None = None
    player_id: hikari.Snowflake | None = None
    name: str | None = None

    _guild_str: str | None = None

    _characters: list[int] | None = None
    _wishlist: list[int] | None = None

    _currency: int | None = None
    _rolls: int | None = None
    _claims: int | None = None

    _rolls_claimed_time: int | None = None
    _daily_claimed_time: int | None = None

    _upgrades: dict[Upgrades, int] | None = None

    def __init__(self, guild_id: hikari.Snowflake, user: hikari.User, model):
        self.guild = guild_id
        self.player_id = user.id
        self._guild_str = f"players_{guild_id}"
        self.name = user.username
        self.model: Model = model

    async def add_player_to_db(self):
        await self.model.dbpool.execute(
            f"INSERT INTO {self._guild_str} VALUES ($1,'',$2,3,0,10,0,'','') ON CONFLICT DO NOTHING",
            str(self.player_id),
            0,
        )

    async def _fetch(self, param: t.Any, field: str) -> t.Any:
        if self.model.dbpool is None:
            return None

        if param is None:
            records = await self.model.dbpool.fetch(
                f"SELECT {field} FROM {self._guild_str} WHERE ID = $1", str(
                    self.player_id)
            )
            return records[0][field]
        return param

    async def _execute(self, value: t.Any, field: str) -> str | None:
        if self.model.dbpool is None:
            return None

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
        if self._rolls:
            self._rolls = value

    @property
    async def rolls_claimed_time(self) -> int:
        return await self._fetch(self._rolls_claimed_time, "claimed_rolls")

    async def set_rolls_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_rolls")
        self._rolls_claimed_time = value
        if self._rolls_claimed_time:
            self._rolls_claimed_time = value

    @property
    async def claims(self) -> int:
        return await self._fetch(self._claims, "claims")

    async def set_claims(self, value: int) -> None:
        await self._execute(value, "claims")
        if self._claims:
            self._claims = value

    @property
    async def daily_claimed_time(self) -> int:
        return await self._fetch(self._daily_claimed_time, "claimed_daily")

    async def set_daily_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_daily")
        if self._daily_claimed_time:
            self._daily_claimed_time = value

    @property
    async def currency(self) -> int:
        return await self._fetch(self._currency, "currency")

    async def set_currency(self, value: int) -> None:
        await self._execute(value, "currency")
        if self._currency:
            self._currency = value

    async def _fetch_int_group(self, param: t.Any, field: str) -> list[int]:
        if self.model.dbpool is None:
            return []

        if param is None:
            record = await self.model.dbpool.fetch(
                f"SELECT {field} FROM {self._guild_str} WHERE ID = $1", str(
                    self.player_id)
            )
            character_str = record[0][field]
            character_ids_list = character_str.split(",")
            filtered_list = filter(lambda x: x != "", character_ids_list)
            return [int(x) for x in filtered_list]
        return param

    async def _set_int_group(self, field: str, value: list[int]) -> None:
        if self.model.dbpool is None:
            return None

        stringified_value = ",".join([str(x) for x in value])

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                stringified_value,
                str(self.player_id),
            )

    async def _append_to_chararacter_list(self, list: list[int], character: Character, field: str, index=None) -> None:
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            if index is None:
                list.append(character.id)
            else:
                list.insert(index, character.id)

            stringified_list = ",".join(map(str, list))

            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                stringified_list,
                str(self.player_id),
            )

    async def _remove_from_character_list(self, list, character: Character, field: str):
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            list.remove(character.id)

            stringified_list = ",".join(map(str, list))

            await conn.execute(
                f"UPDATE {self._guild_str} SET {field} = $1 WHERE ID = $2",
                stringified_list,
                str(self.player_id),
            )

    @property
    async def characters(self) -> list[int]:
        return await self._fetch_int_group(self._characters, "characters")

    async def append_to_characters(self, character: Character, index=None):
        self._characters = await self._fetch_int_group(self._characters, "characters")
        await self._append_to_chararacter_list(self._characters, character, "characters", index=index)
        self._characters = await self._fetch_int_group(self._characters, "characters")

    async def remove_from_characters(self, character: Character):
        self._characters = await self._fetch_int_group(self._characters, "characters")
        await self._remove_from_character_list(self._characters, character, "characters")
        self._characters = await self._fetch_int_group(self._characters, "characters")

    @property
    async def wishlist(self) -> list[int]:
        return await self._fetch_int_group(self._wishlist, "wishlist")

    async def append_to_wishlist(self, character: Character):
        self._wishlist = await self._fetch_int_group(self._wishlist, "wishlist")
        await self._append_to_chararacter_list(self._wishlist, character, "wishlist")
        self._wishlist = await self._fetch_int_group(self._wishlist, "wishlist")

    async def remove_from_wishlist(self, character: Character):
        self._wishlist = await self._fetch_int_group(self._wishlist, "wishlist")
        await self._remove_from_character_list(self._wishlist, character, "wishlist")
        self._wishlist = await self._fetch_int_group(self._wishlist, "wishlist")

    async def reorder(self, character: Character, insertion_index: int):
        await self.remove_from_characters(character)
        await self.append_to_characters(character, index=insertion_index)

    @property
    async def upgrades(self) -> dict[Upgrades, int]:
        upgrades = await self._fetch_int_group(self._upgrades, "upgrades")
        if upgrades == []:
            upgrades = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0]

        upgrades_dict = {
            Upgrades.ROLL_REGEN: upgrades[0],
            Upgrades.ROLL_MAX: upgrades[1],
            Upgrades.DAILY_BONUS: upgrades[2],
            Upgrades.FRAGMENT_BONUS: upgrades[3],
            Upgrades.WISHLIST_SIZE: upgrades[4],
            Upgrades.WISHLIST_RATE_BONUS: upgrades[5],
        }

        return upgrades_dict

    async def increase_upgrade_level(self, index: Upgrades) -> None:
        upgrades = await self.upgrades
        upgrades[index] = upgrades[index] + 1

        new_combined_list = [
            upgrades[Upgrades.ROLL_REGEN],
            upgrades[Upgrades.ROLL_MAX],
            upgrades[Upgrades.DAILY_BONUS],
            upgrades[Upgrades.FRAGMENT_BONUS],
            upgrades[Upgrades.WISHLIST_SIZE],
            upgrades[Upgrades.WISHLIST_RATE_BONUS],
            0,
            0,
            0,
            0,
        ]

        await self._set_int_group("upgrades", new_combined_list)

    async def get_upgrade_shop_objects(self) -> list[items.Upgrade]:
        upgrades = await self.upgrades
        return [
            items.RollGenerationRate(level=upgrades[Upgrades.ROLL_REGEN]),
            items.RollMaximum(level=upgrades[Upgrades.ROLL_MAX]),
            items.FragmentBonus(level=upgrades[Upgrades.FRAGMENT_BONUS]),
            items.DailyBounty(level=upgrades[Upgrades.DAILY_BONUS]),
            items.WishlistSize(level=upgrades[Upgrades.WISHLIST_SIZE]),
            items.WishlistRateUp(level=upgrades[Upgrades.WISHLIST_RATE_BONUS]),
        ]

    async def get_upgrade_value(self, value: Upgrades) -> int | float:
        upgrades = await self.upgrades
        output = UpgradeEffects.upgrades[value].modifier(upgrades[value])
        return output
