from __future__ import annotations

import math
import typing as t

import asyncpg

import hikari
import crescent
import miru
from miru.ext import nav
from bot.character import Character

class CharacterInstance(Character):
    def __init__(self, ctx: crescent.Context, character: Character, model):
        self.guild = hikari.Snowflake(ctx.guild_id)
        self._guild_str = f"players_{hikari.Snowflake(ctx.guild_id)}"
        self.character = character
        self.model = model

    async def _select_user_ids_from_list(self, list) -> list[int]:
        records = await self.model.dbpool.fetch(f"SELECT id, {list} FROM {self._guild_str}")
        users = []
        for record in records:
            if str(self.character.id) in record[list]:
                users.append(record["id"])
        return users

    async def get_wished_ids(self) -> list[int]:
        return await self._select_user_ids_from_list("wishlist")

    async def get_claimed_id(self) -> int:
        """Return the player ID if the character is claimed. If else, return 0."""
        ids = await self._select_user_ids_from_list("characters")
        if len(ids) == 0:
            return 0
        return int(ids[0])
    