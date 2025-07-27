import discord
from discord.ext import commands
from src.utils.localization import localization
import src.utils.config as config


class Utility(commands.Cog):
    def __init__(self, bot):
        self.bot = bot


    @commands.command(name="help")
    async def help(self, ctx, *args):
        """display help information for commands"""
        lang = config.get_user_config(ctx.author.id, "language") or "en"
        if args and args[-1] in localization.languages:
            lang = args[-1]
            args = args[:-1]

        if ctx.guild:
            prefix = config.get_guild_config(ctx.guild.id, "prefix") or "y;"
        else:
            prefix = "y;"
        
        help_data = localization.languages.get(lang, {}).get("help", {})
        default_lang_data = localization.languages.get("en", {}).get("help", {})

        if args:
            command = args[0]
            command_data = help_data.get(command) or default_lang_data.get(command)
            if not command_data:
                await ctx.send(f"no help entry found for `{command}`")
                return
            
            desc = command_data.get("description", "no description available")
            details = command_data.get("details", "")
            args_list = command_data.get("args", [])

            embed = discord.Embed(
                title=f"!{command} {' '.join(args_list)}",
                description=desc,
                color=discord.Color.purple()
            )
            if details:
                while details:
                    chunk = details[:1024]
                    details = details[1024:]
                    embed.add_field(name="info:", value=chunk, inline=False)
                    
            await ctx.send(embed=embed)
            return

        embed = discord.Embed(
            title=help_data.get("help", {}).get("title", "Help"),
            description=help_data.get("help", {}).get("details", "use !help <command> to learn more"),
            color=discord.Color.purple()
        )

        for name, data in help_data.items():
            if name == "help" or name == "placeholders":
                continue
            if not isinstance(data, dict):
                continue
            cmd_args = " ".join(data.get("args", []))
            cmd_desc = data.get("description", "")
            embed.add_field(name=f"{prefix}{name} {cmd_args}", value=cmd_desc, inline=False)

        await ctx.send(embed=embed)
        
    
    @commands.command(name="ping")
    async def ping(self, ctx, arg=None):
        """check the bots response time"""
        langs = ", ".join(localization.languages.keys())
        lang = config.get_user_config(ctx.author.id, "language")
        channel = ctx.channel
        if arg:
            if arg in langs:
                lang = arg
            elif ctx.message.channel_mentions:
                channel = ctx.message.channel_mentions[0]
        response = localization.get("utility", "ping.pong", lang)
        await channel.send(response)


async def setup(bot):
    await bot.add_cog(Utility(bot))
