import logging
import os
import typing as t

import asyncpg
import hikari
import crescent

from bot.utils import Utils
from bot.dbsearch import DBSearch

logger = logging.getLogger(__name__)


class Model:
    def __init__(self, bot: hikari.GatewayBot) -> None:
        self.guilds: list[hikari.Snowflake] = []
        self._dbpool = None
        self.bot = bot
        self.utils = Utils(self)
        self.dbsearch = DBSearch(self)
        self.Plugin = Plugin

        bot.subscribe(hikari.StartingEvent, self.on_starting)
        bot.subscribe(hikari.StoppedEvent, self.on_stop)
        bot.subscribe(hikari.ShardReadyEvent, self.reset_guild_counter)
        bot.subscribe(hikari.GuildJoinEvent, self.increment_guild_counter)
        bot.subscribe(hikari.GuildLeaveEvent, self.decrement_guild_counter)

    async def reset_guild_counter(self, event: hikari.ShardReadyEvent) -> None:
        self.guilds = t.cast(list, event.unavailable_guilds)
        await self.create_schema()

    async def increment_guild_counter(self, event: hikari.GuildJoinEvent) -> None:
        self.guilds.append(event.guild_id)
        await self.create_schema()

    async def decrement_guild_counter(self, event: hikari.GuildLeaveEvent) -> None:
        self.guilds.remove(event.guild_id)

    async def create_schema(self) -> None:
        """
        Create the initial database schema.
        """
        guilds = self.guilds
        logger.info(f"Current guilds: {guilds}")

        self._dbpool = await asyncpg.create_pool(
            dsn=f"postgresql://{os.environ['DATABASE_USER']}:{os.environ['DATABASE_PASSWORD']}@{os.environ['DATABASE_HOST']}:{os.environ['DATABASE_PORT']}/{os.environ['DATABASE']}",
        )

        if self._dbpool is None:
            return

        async with self.dbpool.acquire() as conn:
            await conn.execute("CREATE TABLE IF NOT EXISTS servers (id varchar(31), PRIMARY KEY (id))")

            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS players (guild_id varchar(31) REFERENCES servers(id), player_id varchar(31), currency int, claims int, claimed_daily int, rolls int, claimed_rolls int, PRIMARY KEY (guild_id,player_id))"
            )
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS claimed_characters (character_id int REFERENCES characters(id), guild_id varchar(31), player_id varchar(31), list_order int, default_image int, embed_color varchar(7), PRIMARY KEY (guild_id,character_id), FOREIGN KEY (guild_id,player_id) REFERENCES players(guild_id,player_id))"
            )
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS wishlists (character_id int REFERENCES characters(id), guild_id varchar(31), player_id varchar(31), points smallint, PRIMARY KEY (character_id,guild_id,player_id), FOREIGN KEY (guild_id,player_id) REFERENCES players(guild_id,player_id))"
            )
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS upgrades (guild_id varchar(31), player_id varchar(31), roll_regen smallint, roll_max smallint, daily_bonus smallint, fragment_bonus smallint, wishlist_size smallint, wishlist_rate_bonus smallint, PRIMARY KEY (guild_id,player_id), FOREIGN KEY (guild_id,player_id) REFERENCES players(guild_id,player_id))"
            )

            for guild_id in guilds:
                await conn.execute(f"INSERT INTO servers VALUES ({guild_id}) ON CONFLICT DO NOTHING")

    @property
    def dbpool(self) -> asyncpg.Pool:
        assert self._dbpool, "DBPool should have been created"
        return self._dbpool

    async def on_starting(self, _: hikari.StartingEvent) -> None:
        """
        This function is called when your bot is starting up. This is a good place
        to put initialization functions for the model class.
        """
        ...

    async def on_stop(self, _: hikari.StoppedEvent) -> None:
        """
        This function is called when your bot stops. This is a good place to put
        cleanup functions for the model class.
        """

        if self.dbpool is None:
            return

        await self.dbpool.close()


Plugin = crescent.Plugin[hikari.GatewayBot, Model]
