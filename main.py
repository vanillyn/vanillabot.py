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


@bot.event
async def setup_hook():
    for cog in os.listdir("./src/cogs"):
        if cog.endswith(".py"):
            try:
                await bot.load_extension(f"src.cmds.{cog}")
                print(f"Loaded {cog}")
            except Exception as e:
                print(f"Failed to load {cog}:", e)


token = os.getenv("BOT_TOKEN")
bot.run(token)
