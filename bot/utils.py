import csv
import typing as t

import crescent
import hikari

from bot.character import Character
from bot.user import User

if t.TYPE_CHECKING:
    from bot.model import Model


# NOTE: This is used outside this file.
CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE = "You must in a guild to use this command."


async def guild_only(ctx: crescent.Context) -> crescent.HookResult | None:
    if not ctx.guild_id:
        await ctx.respond(CAN_NOT_BE_USED_OUTSID_GUILD_MESSAGE)
        return crescent.HookResult(exit=True)
    return None


class Utils:
    """A class containing utility functions for the bot."""

    def __init__(self, model) -> None:
        self.model: Model = model

    async def validate_id_in_list(self, ctx: crescent.Context, user: User, char_id: int) -> Character | None:
        if not ctx.guild_id:
            return None

        selected_character = await self.model.dbsearch.create_character_from_id(ctx.guild_id, char_id)

        user_character_ids = await user.characters

        if not selected_character:
            await ctx.respond(f"{char_id} is not a valid ID!")
            return None

        if char_id not in user_character_ids:
            await ctx.respond(
                f"**{selected_character.first_name} {selected_character.last_name}** is not in your list!"
            )
            return None

        return selected_character

    async def validate_search_in_list(self, ctx: crescent.Context, user: User, char_search: str) -> Character | None:
        if not ctx.guild_id:
            return None

        selected_character = await self.model.dbsearch.create_character_from_search(ctx.guild_id, char_search)
        user_character_ids = await user.characters

        if len(selected_character) == 0:
            await ctx.respond(f"Your query `{char_search}` did not return any results.")
            return None

        if len(selected_character) > 1:
            await ctx.respond(f"Your query `{char_search}` returned more than one result.")
            return None

        if selected_character[0].id not in user_character_ids:
            await ctx.respond(
                f"**{selected_character[0].first_name} {selected_character[0].last_name}** is not in your list!"
            )
            return None

        return selected_character[0]

    async def add_characters_to_db(self) -> None:
        if self.model.dbpool is None:
            return

        async with self.model.dbpool.acquire() as conn:
            f = open("bot/data/db.csv", "r", encoding="utf8")
            reader = csv.reader(f, delimiter="|")
            next(reader)
            data = []
            for x in reader:
                try:
                    data.append([int(x[0]), x[1], x[2], x[3],
                                x[4], int(x[5]), x[6], x[7]])
                except IndexError:
                    print(f"Error adding: {x}")

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

    async def character_search_autocomplete(
        self, ctx: crescent.AutocompleteContext, option: hikari.AutocompleteInteractionOption
    ) -> list[tuple[str, str]]:
        options = ctx.options

        if len(options["search"]) == 0:
            return []

        if not ctx.guild_id:
            return []

        character_list = await self.model.dbsearch.create_character_from_search(ctx.guild_id, options["search"])

        output = []
        for character in character_list:
            name = f"{character.first_name} {character.last_name} ({character.get_series()[0]})"
            if len(name) > 100:
                name = name[0:98] + "..."
            output.append((name, str(character.id)))
        return output

    async def character_search_in_list_autocomplete(
        self, ctx: crescent.AutocompleteContext, option: str = "search", char_filter=None,
    ) -> list[tuple[str, str]]:

        if not ctx.guild_id:
            return []

        options = ctx.options
        user = await self.model.dbsearch.create_user(ctx.guild_id, ctx.user)
        if char_filter is None:
            char_filter = await user.characters
        character_list = await self.model.dbsearch.create_character_from_search(
            ctx.guild_id,
            options[option],
            filter=char_filter
        )

        output = []
        for character in character_list:
            name = f"{character.first_name} {character.last_name} ({character.get_series()[0]})"
            if len(name) > 100:
                name = name[0:98] + "..."
            output.append((name, str(character.id)))
        return output

    async def get_users_from_old_guild_table(self, guild: str):
        records = await self.model.dbpool.fetch(
            f"SELECT * FROM players_{guild}"
        )
        return records
