import os

import crescent
import dotenv
import hikari
import miru

from bot.model import Model

dotenv.load_dotenv()

bot = hikari.GatewayBot(os.environ["TOKEN"])
miru.install(bot)

model = Model(bot)

client = crescent.Client(bot, model)
client.plugins.load_folder("bot.plugins")


bot.run()
