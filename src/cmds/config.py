import discord
from discord.ext import commands
from src.utils import config as cfg
from src.utils.localization import localization

class Config(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="config")
    @commands.has_permissions(administrator=True)
    async def config(self, ctx, option: str = None, *, value: str = None):
        lang = await cfg.get_language(ctx.guild.id)

        if not option or not value:
            return await ctx.send(localization.get("config.usage", lang=lang))

        option = option.lower()

        if option == "log_channel":
            if ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
                await cfg.set_log_channel(ctx.guild.id, channel.id)
                await ctx.send(localization.get("config.log_channel.set", lang=lang, channel=channel.mention))
            else:
                await ctx.send(localization.get("config.log_channel.invalid", lang=lang))

        elif option == "log_language":
            if value in localization.languages:
                await cfg.set_language(ctx.guild.id, value)
                await ctx.send(localization.get("config.log_language.set", lang=value, lang_name=value))
            else:
                await ctx.send(localization.get("error.invalid_language", lang=lang, available=", ".join(localization.languages.keys())))
        else:
            await ctx.send(localization.get("config.unknown_option", lang=lang, option=option))

async def setup(bot):
    await bot.add_cog(Config(bot))
