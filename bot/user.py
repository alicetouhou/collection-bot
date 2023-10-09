import typing as t

from bot.character import Character
from bot.character_instance import CharacterInstance
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

    _characters: list[int] = []
    _wishlist: list[int] = []

    _currency: int = 0
    _rolls: int = 0
    _claims: int = 0

    _rolls_claimed_time: int = 0
    _daily_claimed_time: int = 0

    _upgrades: dict[Upgrades, int] = {}

    def __init__(self, guild_id: hikari.Snowflake, user: hikari.User, model):
        self.guild = guild_id
        self.player_id = user.id
        self.name = user.username
        self.model: Model = model

    async def add_player_to_db(self) -> None:
        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO players VALUES ($1,$2,$3,3,0,10,0) ON CONFLICT DO NOTHING",
                str(self.guild),
                str(self.player_id),
                0,
            )

    async def add_upgrades(self) -> None:
        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"INSERT INTO upgrades VALUES ($1,$2,0,0,0,0,0,0) ON CONFLICT DO NOTHING",
                str(self.guild),
                str(self.player_id),
            )

    async def populate(self) -> None:
        if self.model.dbpool is None:
            return

        records = await self.model.dbpool.fetch(
            f"""SELECT players.rolls, players.claims, players.claimed_rolls, players.claimed_daily, players.currency,
            upgrades.*, claimed_characters.list_order,
            claimed_characters.character_id AS claimed_character_id, wishlists.character_id AS wishlist_character_id
            FROM players
            LEFT JOIN upgrades ON upgrades.player_id = players.player_id AND upgrades.guild_id = players.guild_id
            LEFT JOIN claimed_characters ON claimed_characters.player_id = players.player_id AND claimed_characters.guild_id = players.guild_id
            LEFT JOIN wishlists ON wishlists.player_id = players.player_id AND wishlists.guild_id = players.guild_id
            WHERE players.guild_id = $1 AND players.player_id = $2 ORDER BY list_order""",
            str(self.guild),
            str(self.player_id)
        )

        character_list = []
        wishlist_list = []

        for record in records:
            if record["claimed_character_id"] not in character_list:
                character_list.append(record["claimed_character_id"])
            if record["wishlist_character_id"] not in wishlist_list:
                wishlist_list.append(record["wishlist_character_id"])

        if len(records) == 0:
            await self.add_player_to_db()

        self._rolls = records[0]["rolls"]
        self._claims = records[0]["claims"]
        self._rolls_claimed_time = records[0]["claimed_rolls"]
        self._daily_claimed_time = records[0]["claimed_daily"]
        self._currency = records[0]["currency"]

        self._characters = character_list
        self._wishlist = wishlist_list

        if records[0]["roll_regen"] == None:
            await self.add_upgrades()
            self._upgrades = {
                Upgrades.ROLL_REGEN: 0,
                Upgrades.ROLL_MAX: 0,
                Upgrades.DAILY_BONUS: 0,
                Upgrades.FRAGMENT_BONUS: 0,
                Upgrades.WISHLIST_SIZE: 0,
                Upgrades.WISHLIST_RATE_BONUS: 0,
            }
        else:
            self._upgrades = {
                Upgrades.ROLL_REGEN: records[0]["roll_regen"],
                Upgrades.ROLL_MAX: records[0]["roll_max"],
                Upgrades.DAILY_BONUS: records[0]["daily_bonus"],
                Upgrades.FRAGMENT_BONUS: records[0]["fragment_bonus"],
                Upgrades.WISHLIST_SIZE: records[0]["wishlist_size"],
                Upgrades.WISHLIST_RATE_BONUS: records[0]["wishlist_rate_bonus"],
            }

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
    def rolls(self) -> int:
        return self._rolls

    async def set_rolls(self, value: int) -> None:
        await self._execute(value, "rolls")
        self._rolls = value
        if self._rolls:
            self._rolls = value

    @property
    def rolls_claimed_time(self) -> int:
        return self._rolls_claimed_time

    async def set_rolls_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_rolls")
        self._rolls_claimed_time = value
        if self._rolls_claimed_time:
            self._rolls_claimed_time = value

    @property
    def claims(self) -> int:
        return self._claims

    async def set_claims(self, value: int) -> None:
        await self._execute(value, "claims")
        if self._claims:
            self._claims = value

    @property
    def daily_claimed_time(self) -> int:
        return self._daily_claimed_time

    async def set_daily_claimed_time(self, value: int) -> None:
        await self._execute(value, "claimed_daily")
        if self._daily_claimed_time:
            self._daily_claimed_time = value

    @property
    def currency(self) -> int:
        return self._currency

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

        async with self.model.dbpool.acquire() as conn:
            await conn.execute(
                f"UPDATE upgrades SET {upgrades_name[upgrade]} = $1 WHERE guild_id = $2 AND player_id = $3",
                self.upgrades[upgrade] + amount,
                str(self.guild),
                str(self.player_id),
            )

    @property
    def characters(self) -> list[int]:
        return self._characters

    async def append_to_characters(self, character: Character):
        await self._append_to_chararacter_list(character)
        self._characters = await self._fetch_character_list()

    async def remove_from_characters(self, character: Character):
        await self._remove_from_character_list(character)
        self._characters = await self._fetch_character_list()

    async def move_to_top(self, character: Character):
        await self._move_to_top(character)

    async def set_top_chars(self, char_list: list[Character] | list[CharacterInstance], indices: list[int]) -> None:
        if self.model.dbpool is None:
            return None

        if len(char_list) != len(indices):
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

        executelist = []
        for i in range(0, len(indices)):
            executelist.append([indices[i] + new_index - len(indices),
                               char_list[len(indices)-1-i].id, str(self.guild), str(self.player_id)])

        async with self.model.dbpool.acquire() as conn:
            await conn.executemany(
                f"UPDATE claimed_characters SET list_order = $1 WHERE character_id = $2 AND guild_id = $3 AND player_id = $4",
                executelist,
            )

    @property
    def wishlist(self) -> list[int]:
        return self._wishlist

    async def append_to_wishlist(self, character: Character):
        await self._append_to_wishlist(character)
        self._characters = await self._fetch_wishlist()

    async def remove_from_wishlist(self, character: Character):
        await self._remove_from_wishlist(character)
        self._characters = await self._fetch_wishlist()

    @property
    def upgrades(self) -> dict[Upgrades, int]:
        return self._upgrades

    async def increase_upgrade_level(self, upgrade: Upgrades, amount: int = 1) -> None:
        await self._increase_upgrade_level(upgrade, amount)

    async def get_upgrade_shop_objects(self) -> list[items.Upgrade]:
        return [
            items.RollGenerationRate(level=self.upgrades[Upgrades.ROLL_REGEN]),
            items.RollMaximum(level=self.upgrades[Upgrades.ROLL_MAX]),
            items.FragmentBonus(level=self.upgrades[Upgrades.FRAGMENT_BONUS]),
            items.DailyBounty(level=self.upgrades[Upgrades.DAILY_BONUS]),
            items.WishlistSize(level=self.upgrades[Upgrades.WISHLIST_SIZE]),
            items.WishlistRateUp(
                level=self.upgrades[Upgrades.WISHLIST_RATE_BONUS]),
        ]

    def get_upgrade_value(self, value: Upgrades) -> int | float:
        output = UpgradeEffects.upgrades[value].modifier(self.upgrades[value])
        return output
