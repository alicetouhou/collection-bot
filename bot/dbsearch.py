import csv
import typing as t

from bot.character import Character
from bot.character_instance import CharacterInstance
from bot.user import User

import crescent
import hikari

if t.TYPE_CHECKING:
    from bot.model import Model

class DBSearch:
    
    def __init__(self, model):
        self.model = model

    async def create_user(self, context: crescent.Context, player_id) -> User:
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

    async def create_random_character(self, context) -> CharacterInstance:
        records = await self.model.dbpool.fetch(
            "SELECT * FROM characters ORDER BY RANDOM() LIMIT 1",
        )
        character = Character.from_record(records[0])
        instance = CharacterInstance(context, character, self.model)
        return instance
    