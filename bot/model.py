import hikari
import bot

class Model:
    guilds = []

    async def reset_guild_counter(self, event: hikari.ShardReadyEvent) -> None:
        self.guilds = event.unavailable_guilds
        self.ensure_dbs_exist()


    async def increment_guild_counter(self, event: hikari.GuildJoinEvent) -> None:
        self.guild.append(event.guild_id)
        self.ensure_dbs_exist()


    async def decrement_guild_counter(self, event: hikari.GuildLeaveEvent) -> None:
        self.guild.remove(event.guild_id)

    def __init__(self) -> None:
        ...

    def ensure_dbs_exist(self):
        servers = self.guilds
        print(f"Current guilds: {servers}")
        with bot.dbpool.db_cursor() as cur:
                cur.execute("CREATE TABLE IF NOT EXISTS servers (ID varchar(31), PRIMARY KEY (ID))")
                for server in servers:
                    cur.execute(
                        f"CREATE TABLE IF NOT EXISTS players_{str(server)} (ID varchar(31), characters varchar(65535), currency int, claims int, claimed_daily int, rolls int, claimed_rolls int, wishlist varchar(1027), upgrades varchar(2055), PRIMARY KEY (ID))"
                    )
                    cur.execute(
                        f"INSERT INTO servers VALUES ({str(server)}) ON CONFLICT DO NOTHING"
                    )

    async def on_start(self, _: hikari.StartedEvent) -> None:
        ...

    async def on_stop(self, _: hikari.StoppedEvent) -> None:
        """
        This function is called when your bot stops. This is a good place to put
        cleanup functions for the model class.
        """
        ...