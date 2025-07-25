import discord
from discord.ext import commands
import time
from time import perf_counter
from src.utils.localization import localization
from src.utils.config import get_config_value


class Ping(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        @bot.command(name="ping")
        async def ping(ctx, arg=None):
            start_time = time.time()

            langs = ", ".join(localization.languages.keys())

            lang = get_config_value(ctx.guild.id, "log_language") or "en"
            channel = ctx.channel
            debug = False

            if arg:
                if arg in langs:
                    lang = arg
                elif arg.lower() == "debug":
                    debug = True
                elif ctx.message.channel_mentions:
                    channel = ctx.message.channel_mentions[0]

            response_time = int((time.time() - start_time) * 1000)
            response = localization.get("ping.pong", lang).format(ms=response_time)

            await channel.send(response)

            if debug:
                debug_msg = "\n".join(
                    [
                        f"response time: {response_time}ms",
                        f"used lang: {lang}",
                        f"loaded langs: {', '.join(langs)}",
                    ]
                )
                await channel.send(debug_msg)


async def setup(bot):
    await bot.add_cog(Ping(bot))
