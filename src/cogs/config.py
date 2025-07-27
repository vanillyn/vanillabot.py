import discord
import logging
from discord.ext import commands
from src.utils.config import set_guild_config, get_guild_config, set_user_config, get_user_config
from src.utils.localization import supported_languages

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class ConfigCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name='config', invoke_without_command=True)
    async def config(self, ctx):
        """config command group"""
        embed = discord.Embed(
            title="Configuration Commands",
            description="Available configuration options:",
            color=0x00ff00
        )
        embed.add_field(
            name="User Settings",
            value="`config user language <lang>` - Set your language preference",
            inline=False
        )
        embed.add_field(
            name="Server Settings (`Manage Server` required.)",
            value="`config server prefix <prefix>` - Set prefix\n"
                  "`config server language <lang>` - Set server default language",
            inline=False
        )
        embed.add_field(
            name="Available Languages",
            value=f"Currently supported languages: {', '.join(supported_languages)}\n[Contribute to add your own language!](https://github.com/vanillyn/vanillabot.py)",
            inline=False
        )
        embed.add_field(
            name="View Settings",
            value="`config view` - View current settings",
            inline=False
        )
        await ctx.send(embed=embed)

    @config.group(name='user', invoke_without_command=True)
    async def config_user(self, ctx):
        """User configuration commands"""
        embed = discord.Embed(
            title="User Configuration",
            description="Available user settings:",
            color=0x0099ff
        )
        embed.add_field(
            name="Language",
            value="`config user language <lang>` - Set your language preference",
            inline=False
        )
        await ctx.send(embed=embed)

    @config_user.command(name='language')
    async def set_user_language(self, ctx, language: str):
        """set user language"""

        if language.lower() not in supported_languages:
            embed = discord.Embed(
                title="Invalid Language",
                description=f"Currently supported languages: {', '.join(supported_languages)}\n[Contribute to add your own language!](https://github.com/vanillyn/vanillabot.py)",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        try:
            set_user_config(ctx.author.id, 'language', language.lower())
            embed = discord.Embed(
                title="Language Updated",
                description=f"Your language has been set to `{language.lower()}`",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to update user language: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update your language preference.\nError: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @config.group(name='server', invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def config_server(self, ctx):
        """server configuration commands"""
        embed = discord.Embed(
            title="Server Configuration",
            description="Available server settings:",
            color=0xff9900
        )
        embed.add_field(
            name="Prefix",
            value="`config server prefix <prefix>` - Set prefix",
            inline=False
        )
        embed.add_field(
            name="Language",
            value="`config server language <lang>` - Set language",
            inline=False
        )
        await ctx.send(embed=embed)

    @config_server.command(name='prefix')
    @commands.has_permissions(manage_guild=True)
    async def set_server_prefix(self, ctx, prefix: str):
        if len(prefix) > 5:
            embed = discord.Embed(
                title="Invalid Prefix",
                description="Prefix must be 5 characters or less.",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        try:
            set_guild_config(ctx.guild.id, 'prefix', prefix)
            embed = discord.Embed(
                title="Prefix Updated",
                description=f"Server prefix has been set to `{prefix}`",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to update server prefix: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update server prefix.\nError: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @config_server.command(name='language')
    @commands.has_permissions(manage_guild=True)
    async def set_server_language(self, ctx, language: str):
        
        if language.lower() not in supported_languages or None:
            embed = discord.Embed(
                title="Invalid Language",
                description=f"Currently supported languages: {', '.join(supported_languages)}\n[Contribute to add your own language!](https://github.com/vanillyn/vanillabot.py)",
                color=0xff0000
            )
            await ctx.send(embed=embed)
            return

        try:
            set_guild_config(ctx.guild.id, 'language', language.lower())
            embed = discord.Embed(
                title="Language Updated",
                description=f"Server language has been set to `{language.lower()}`",
                color=0x00ff00
            )
            await ctx.send(embed=embed)
        except Exception as e:
            logger.error(f"Failed to update server language: {e}")
            embed = discord.Embed(
                title="Error",
                description=f"Failed to update server language.\nError: {str(e)}",
                color=0xff0000
            )
            await ctx.send(embed=embed)

    @config.command(name='view')
    async def view_config(self, ctx):
        embed = discord.Embed(
            title="Current Configuration",
            color=0x9932cc
        )
        
        user_language = get_user_config(ctx.author.id, 'language') or 'en'
        embed.add_field(
            name="Your Settings",
            value=f"Language: `{user_language}`",
            inline=False
        )
        
        if ctx.guild:
            server_prefix = get_guild_config(ctx.guild.id, 'prefix') or 'y;'
            server_language = get_guild_config(ctx.guild.id, 'language') or 'en'
            embed.add_field(
                name="Server Settings",
                value=f"Prefix: `{server_prefix}`\nLanguage: `{server_language}`",
                inline=False
            )
        
        await ctx.send(embed=embed)

    @config_server.error
    async def config_server_error(self, ctx, error):
        if isinstance(error, commands.MissingPermissions):
            embed = discord.Embed(
                title="No Permission.",
                description="You need the 'Manage Server' permission to change server settings.",
                color=0xff0000
            )
            await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ConfigCog(bot))