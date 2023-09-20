from __future__ import annotations
import hikari
import typing as t
from bot.character import Character

if t.TYPE_CHECKING:
    from bot.model import Model

class CharacterInstance(Character):
    def __init__(self, guild_id: hikari.Snowflake, character: Character, model: Model):
        self.guild_id = guild_id
        self._guild_str = f"players_{guild_id}"
        self.model = model
        super().__init__(
            first_name=character.first_name,
            last_name=character.last_name,
            anime=character.anime,
            manga=character.manga,
            games=character.games,
            images=character.images,
            id=character.id,
            favorites=character.value,
        )

    async def _select_user_ids_from_list(self, list) -> list[int]:
        records = await self.model.dbpool.fetch(f"SELECT id, {list} FROM {self._guild_str}")
        users = []
        for record in records:
            if str(self.id) in record[list].split(","):
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

    async def _get_embed(self, image) -> hikari.Embed:
        embed = await super()._get_embed(image)
        claimed_person_id = await self.get_claimed_id()
        if claimed_person_id == 0:
            return embed
        claimed_person = self.model.bot.cache.get_member(self.guild_id, claimed_person_id)
        if not claimed_person:
            claimed_person = await self.model.bot.rest.fetch_member(self.guild_id, claimed_person_id)
        if claimed_person:
            embed.set_footer(f"Claimed by {claimed_person.username}", icon=claimed_person.avatar_url)

        return embed
