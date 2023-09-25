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
        self.name = user.username
        self.model: Model = model

    async def add_player_to_db(self):
        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO players VALUES ($1,$2,$3,3,0,10,0) ON CONFLICT DO NOTHING",
                str(self.guild),
                str(self.player_id),
                0,
            )

    async def _fetch(self, param: t.Any, field: str) -> t.Any:
        if self.model.dbpool is None:
            return None

        if param is None:
            records = await self.model.dbpool.fetch(
                f"SELECT {field} FROM players WHERE guild_id = $1 AND player_id = $2",
                str(self.guild),
                str(self.player_id)
            )
            return records[0][field]
        return param

    async def _execute(self, value: t.Any, field: str) -> str | None:
        if self.model.dbpool is None:
            return None

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE players SET {field} = $1 WHERE guild_id = $2 AND player_id = $3",
                value,
                str(self.guild),
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

    async def _fetch_character_list(self) -> list[int]:
        if self.model.dbpool is None:
            return []

        records = await self.model.dbpool.fetch(
            f"SELECT character_id FROM claimed_characters WHERE guild_id = $1 AND player_id = $2 ORDER BY list_order",
            str(self.guild),
            str(self.player_id)
        )
        return [x["character_id"] for x in records]

    async def _append_to_chararacter_list(self, character: Character) -> None:
        if self.model.dbpool is None:
            return

        top_record = await self.model.dbpool.fetchrow(
            f"SELECT list_order FROM claimed_characters WHERE guild_id = $1 AND player_id = $2 ORDER BY list_order DESC LIMIT 1",
            str(self.guild),
            str(self.player_id)
        )

        if top_record:
            new_index = top_record[0] + 1
        else:
            new_index = 0

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO claimed_characters VALUES ($1,$2,$3,$4,0,'F598DF') ON CONFLICT DO NOTHING",
                character.id,
                str(self.guild),
                str(self.player_id),
                new_index
            )

    async def _remove_from_character_list(self, character: Character):
        if self.model.dbpool is None:
            return

        await self.model.dbpool.fetch(
            f"DELETE FROM claimed_characters WHERE character_id = $1 AND guild_id = $2 AND player_id = $3",
            character.id,
            str(self.guild),
            str(self.player_id)
        )

    async def _move_to_top(self, character: Character) -> None:
        if self.model.dbpool is None:
            return None

        top_record = await self.model.dbpool.fetchrow(
            f"SELECT list_order FROM claimed_characters WHERE guild_id = $1 AND player_id = $2 ORDER BY list_order ASC LIMIT 1",
            str(self.guild),
            str(self.player_id)
        )

        if top_record:
            new_index = top_record[0] - 1
        else:
            new_index = -1

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE claimed_characters SET list_order = $1 WHERE character_id = $2 AND guild_id = $3 AND player_id = $4",
                new_index,
                character.id,
                str(self.guild),
                str(self.player_id),
            )

    async def _fetch_wishlist(self) -> list[int]:
        if self.model.dbpool is None:
            return []

        records = await self.model.dbpool.fetch(
            f"SELECT character_id FROM wishlists WHERE guild_id = $1 AND player_id = $2",
            str(self.guild),
            str(self.player_id)
        )
        return [x["character_id"] for x in records]

    async def _append_to_wishlist(self, character: Character) -> None:
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO wishlists VALUES ($1,$2,$3,1) ON CONFLICT DO NOTHING",
                character.id,
                str(self.guild),
                str(self.player_id)
            )

    async def _remove_from_wishlist(self, character: Character):
        if self.model.dbpool is None:
            return

        await self.model.dbpool.fetch(
            f"DELETE FROM wishlists WHERE character_id = $1 AND guild_id = $2 AND player_id = $3",
            character.id,
            str(self.guild),
            str(self.player_id)
        )

    async def _fetch_upgrades(self) -> dict[str, int]:
        if self.model.dbpool is None:
            return {}

        records = await self.model.dbpool.fetch(
            f"SELECT roll_regen,roll_max,daily_bonus,fragment_bonus,wishlist_size,wishlist_rate_bonus FROM upgrades WHERE guild_id = $1 AND player_id = $2",
            str(self.guild),
            str(self.player_id)
        )

        if len(records) == 1:
            return records[0]

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO upgrades VALUES ($1,$2,0,0,0,0,0,0) ON CONFLICT DO NOTHING",
                str(self.guild),
                str(self.player_id),
            )

        return await self._fetch_upgrades()

    async def _increase_upgrade_level(self, upgrade: Upgrades, amount: int) -> None:
        if self.model.dbpool is None:
            return None

        upgrades_name = {
            Upgrades.ROLL_REGEN: "roll_regen",
            Upgrades.ROLL_MAX: "roll_max",
            Upgrades.DAILY_BONUS: "daily_bonus",
            Upgrades.FRAGMENT_BONUS: "fragment_bonus",
            Upgrades.WISHLIST_SIZE: "wishlist_size",
            Upgrades.WISHLIST_RATE_BONUS: "wishlist_rate_bonus",
        }

        upgrades = await self.upgrades

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE upgrades SET {upgrades_name[upgrade]} = $1 WHERE guild_id = $2 AND player_id = $3",
                upgrades[upgrade] + amount,
                str(self.guild),
                str(self.player_id),
            )

    @property
    async def characters(self) -> list[int]:
        return await self._fetch_character_list()

    async def append_to_characters(self, character: Character):
        await self._append_to_chararacter_list(character)
        self._characters = await self._fetch_character_list()

    async def remove_from_characters(self, character: Character):
        await self._remove_from_character_list(character)
        self._characters = await self._fetch_character_list()

    @property
    async def wishlist(self) -> list[int]:
        return await self._fetch_wishlist()

    async def append_to_wishlist(self, character: Character):
        await self._append_to_wishlist(character)
        self._characters = await self._fetch_wishlist()

    async def remove_from_wishlist(self, character: Character):
        await self._remove_from_wishlist(character)
        self._characters = await self._fetch_wishlist()

    async def move_to_top(self, character: Character):
        await self._move_to_top(character)

    @property
    async def upgrades(self) -> dict[Upgrades, int]:
        upgrades = await self._fetch_upgrades()

        upgrades_dict = {
            Upgrades.ROLL_REGEN: upgrades["roll_regen"],
            Upgrades.ROLL_MAX: upgrades["roll_max"],
            Upgrades.DAILY_BONUS: upgrades["daily_bonus"],
            Upgrades.FRAGMENT_BONUS: upgrades["fragment_bonus"],
            Upgrades.WISHLIST_SIZE: upgrades["wishlist_size"],
            Upgrades.WISHLIST_RATE_BONUS: upgrades["wishlist_rate_bonus"],
        }

        return upgrades_dict

    async def increase_upgrade_level(self, upgrade: Upgrades, amount: int = 1) -> None:
        await self._increase_upgrade_level(upgrade, amount)

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
