import discord
from discord.ext import commands
from dotenv import load_dotenv
import logging
import sys
import os
import src.utils.config as db

from src.utils.localization import localization
from src.utils.config.utils import get_guild_config
name = os.getenv("NAME", "berrylyn")
env = os.getenv("ENVIRONMENT", "DEVELOPMENT")

logfile = logging.FileHandler(f'{name}.log')
stdout = logging.StreamHandler(sys.stdout)
logger = logging.getLogger("discord")
logger.addHandler(logfile)
logger.addHandler(stdout)


if env == "DEVELOPMENT":
    logger.setLevel(logging.DEBUG)
    logger.info(f"Running in {env}. Debugging enabled.")
else:
    level = logging.ERROR
    logger.info(f"Running in {env}.")


load_dotenv()
localization.load_languages()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

async def get_prefix(bot, message):
    guild_id = message.guild.id if message.guild else None
    prefix = get_guild_config(guild_id, "prefix")
    if str(prefix) in message.content and env == "DEVELOPMENT":
        logger.debug(f"Command ran '{message.content}' in {message.guild.name}. This is for debugging and should be removed if environment is in production.")
    return commands.when_mentioned_or(prefix or "ly:")(bot, message)



bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)



@bot.event
async def on_ready():
    logger.info(f"{os.getenv('NAME', 'bot')} loaded. {bot.user}")


@bot.event
async def setup_hook():
    for cog in os.listdir("./src/cogs"):
        if cog.endswith(".py") and not cog.startswith("__"):
            try:
                await bot.load_extension(f"src.cogs.{cog[:-3]}")
                logger.info(f"Loaded {cog}")
            except Exception as e:
                logger.error(f"Failed to load {cog}:", e)


@commands.Cog.listener()
async def on_reaction_add(self, reaction, user):
    if user.bot:
        return
    if reaction.message.author.bot:
        if str(reaction.emoji) in ["❌"]:
            await reaction.message.delete()

db.init()
token = os.getenv("BOT_TOKEN")
bot.run(token, log_handler=stdout)
