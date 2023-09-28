from __future__ import annotations
import hikari
import typing as t
from bot.character import Character
from miru.ext import nav
import copy
import asyncpg

if t.TYPE_CHECKING:
    from bot.model import Model


class CharacterInstance(Character):
    def __init__(self, guild_id: hikari.Snowflake, character: Character, model: Model):
        self.guild_id = guild_id
        self.model = model
        self.series_names: list[asyncpg.Record] = []
        super().__init__(
            first_name=character.first_name,
            last_name=character.last_name,
            series=character.series,
            images=character.images,
            id=character.id,
            favorites=character.value,
        )

    async def get_wished_ids(self) -> list[int]:
        """Return all the users in the guild that wished this character."""
        if self.model.dbpool is None:
            return []

        records = await self.model.dbpool.fetch(
            f"SELECT player_id FROM wishlists WHERE guild_id = $1 AND character_id = $2",
            str(self.guild_id),
            self.id
        )
        return [x["player_id"] for x in records]

    async def get_claimed_id(self) -> int:
        """Return the player ID if the character is claimed. If else, return 0."""
        if self.model.dbpool is None:
            return 0

        records = await self.model.dbpool.fetch(
            f"SELECT player_id FROM claimed_characters WHERE guild_id = $1 AND character_id = $2",
            str(self.guild_id),
            self.id
        )

        if records:
            return records[0]["player_id"]
        return 0

    async def get_series(self) -> list[asyncpg.Record]:
        if len(self.series_names) == 0:
            self.series_names = []

            bucket = await self.model.dbpool.fetchval(
                f"SELECT bucket_id FROM buckets WHERE series_id = $1",
                self.series[0]
            )

            if bucket:
                record = await self.model.dbpool.fetchrow(
                    f"SELECT series_name,type FROM series WHERE id = $1",
                    bucket
                )
                self.series_names = [record]
                return self.series_names

            records: list[asyncpg.Record] = []
            for series in self.series:
                record = await self.model.dbpool.fetchrow(
                    f"SELECT series_name,type FROM series WHERE id = $1",
                    series
                )
                records.append(record)
            self.series_names = records
        return self.series_names

    def get_series_icon(self, series: asyncpg.Record):
        if series["type"] == "bucket":
            return "📚"
        if series["type"] == "anime":
            return "🎬"
        if series["type"] == "manga":
            return "📖"
        if series["type"] == "game":
            return "🎮"
        return ""

    async def _get_embed(self, image) -> hikari.Embed:
        name = f"{self.first_name} {self.last_name} • {self.value}<:wishfragments:1148459769980530740>"
        await self.get_series()

        embed = hikari.Embed(title=name, color="f598df",
                             description=",".join([f'{self.get_series_icon(x)} {x["series_name"]}' for x in self.series_names]))
        embed.set_image(image)

        claimed_person_id = await self.get_claimed_id()
        if claimed_person_id == 0:
            return embed
        claimed_person = self.model.bot.cache.get_member(
            self.guild_id, claimed_person_id)
        if not claimed_person:
            claimed_person = await self.model.bot.rest.fetch_member(self.guild_id, claimed_person_id)
        if claimed_person:
            embed.set_footer(
                f"Claimed by {claimed_person.username}", icon=claimed_person.avatar_url)
        return embed

    async def get_navigator(self) -> nav.NavigatorView:
        pages = []
        embed = await self._get_embed(self.images[0])

        for image in self.images:
            new_embed = copy.deepcopy(embed)
            new_embed.set_image(image)
            pages.append(new_embed)

        buttons = [nav.PrevButton(), nav.IndicatorButton(), nav.NextButton()]
        navigator = nav.NavigatorView(pages=pages, buttons=buttons)
        return navigator

    async def get_claimable_embed(self) -> hikari.Embed:
        embed = await self._get_embed(self.images[0])
        return embed
