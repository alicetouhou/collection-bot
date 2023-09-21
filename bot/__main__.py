import os

import crescent
import dotenv
import hikari
import miru

from bot.model import Model

dotenv.load_dotenv(override=True)

bot = hikari.GatewayBot(
    os.environ["TOKEN"], intents=hikari.Intents.GUILD_MESSAGES | hikari.Intents.MESSAGE_CONTENT | hikari.Intents.GUILDS
)
miru.install(bot)

model = Model(bot)

client = crescent.Client(bot, model)
client.plugins.load_folder("bot.plugins")


bot.run()
