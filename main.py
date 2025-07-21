import discord
from discord.ext import commands
from dotenv import load_dotenv
import os

from src.utils.localization import localization

load_dotenv()
localization.load_languages()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

prefix = os.getenv("PREFIX", ";")
bot = commands.Bot(command_prefix=prefix, intents=intents)

@bot.event
async def on_ready():
    print(f"{os.getenv('NAME', 'bot')} loaded. {bot.user}")
    for filename in os.listdir("./src/cmds"):
        if filename.endswith(".py") and not filename.startswith("__"):
            await bot.load_extension(f"src.cmds.{filename[:-3]}")
    print("all berries loaded.")

token = os.getenv("BOT_TOKEN")
bot.run(token)
