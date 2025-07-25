import discord
from discord.ext import commands
from src.utils.config import get_config


async def log_action(bot: commands.Bot, guild: discord.Guild, message: str):
    config = await get_config(guild.id)
    log_channel_id = config.get("log_channel")
    if not log_channel_id:
        return

    log_channel = guild.get_channel(int(log_channel_id))
    if not log_channel:
        return

    await log_channel.send(message)
