import discord
from discord.ext import commands
from dotenv import load_dotenv
import os
import src.utils.config as config

from src.utils.localization import localization
from src.utils.config import get_guild_config

load_dotenv()
localization.load_languages()

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.members = True

async def get_prefix(bot, message):
    guild_id = message.guild.id if message.guild else None
    prefix = get_guild_config(guild_id, "prefix")
    if str(prefix) in message.content and os.getenv('ENVIRONMENT') == "DEVELOPMENT":
        print(f"Command ran '{message.content}' in {message.guild.name}. This is for debugging and should be removed if environment is in production.")
    return commands.when_mentioned_or(prefix or "ly:")(bot, message)

bot = commands.Bot(command_prefix=get_prefix, intents=intents, help_command=None)



@bot.event
async def on_ready():
    print(f"{os.getenv('NAME', 'bot')} loaded. {bot.user}")


@bot.event
async def setup_hook():
    for cog in os.listdir("./src/cogs"):
        if cog.endswith(".py") and not cog.startswith("__"):
            try:
                await bot.load_extension(f"src.cogs.{cog[:-3]}")
                print(f"Loaded {cog}")
            except Exception as e:
                print(f"Failed to load {cog}:", e)


@commands.Cog.listener()
async def on_reaction_add(self, reaction, user):
    if user.bot:
        return
    if reaction.message.author.bot:
        if str(reaction.emoji) in ["❌"]:
            await reaction.message.delete()

config.init_config()
token = os.getenv("BOT_TOKEN")
bot.run(token)
