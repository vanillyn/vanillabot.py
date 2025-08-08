import discord
from discord.ext import commands
import asyncio
import re
from src.utils.localization import localization
from src.utils.placeholders import pl
from src.utils.config.utils import get_guild_triggers, get_all_autoresponders, get_autoresponder, create_autoresponder, update_autoresponder, delete_autoresponder, autoresponder_exists
import src.utils.config.utils as cfg


class AutoresponderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ar_messages = {}

    def check_restricted_placeholders(self, response: str, user: discord.Member) -> tuple[bool, str]:
        """check if response contains restricted placeholders and if user has permission"""
        restricted_patterns = [
            r"\{dm(?::[^}]*)\}",  # {dm} or {dm:target}
            r"\{interaction:[^}]*\}",  # {interaction:type:value[:nametag]}
            r"\{delete\}",  # {delete}
            r"\{action:[^}]*\}",  # {action:action:nametag}
            r"\{role(?::[^:]*):[^}]*\}",  # {role[:action]:role_name}
            r"\{embed:[^}]*\}",  # {embed:name}
            r"\{user_infractions\}",  # staff_placeholders
            r"\{message_id\}", # {message_id}
            r"\{message\}", # {message}
            r"\{message_reactions\}", # {message_reactions}
            r"\{message_created\}", # {message_created}
            r"\{channel_last_message\}", # {channel_last_message}
        ]
        lang = cfg.get_user_config(user.id, "language") or "en"
        for pattern in restricted_patterns:
            if re.search(pattern, response):
                if not user.guild_permissions.manage_guild:
                    return False, localization.get("config", "ar.restricted_placeholders", lang=lang)
        return True, ""

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        user_lang = cfg.get_user_config(message.author.id, "language") or "en"
        triggers = get_guild_triggers(guild_id)

        for ar_data in triggers:
            trigger = ar_data["trigger"].lower()
            content = message.content.lower()

            if trigger in content:
                ar_name = ar_data["name"]
                ar_data_user_lang = get_autoresponder(guild_id, ar_name, user_lang)
                ar_data_en = get_autoresponder(guild_id, ar_name, "en")

                if ar_data_user_lang:
                    data = ar_data_user_lang["response"]
                elif ar_data_en:
                    data = ar_data_en["response"]
                else:
                    continue

                if data:
                    response, reactions = await pl(message, data)

                    if isinstance(response, str):
                        print(f"Failed to process autoresponder '{ar_name}': {response}")
                        break

                    if response:
                        try:
                            sent_message = await message.channel.send(
                                content=response["text"],
                                embed=response.get("embed"),
                                view=response.get("view")
                            )

                            if response.get("delete_after"):
                                await asyncio.sleep(response["delete_after"])
                                await sent_message.delete()
                            
                            self.ar_messages[sent_message.id] = {
                                "name": ar_name,
                                "creator_id": (ar_data_user_lang or ar_data_en)["creator_id"],
                                "trigger": ar_data["trigger"],
                            }
                        except discord.Forbidden:
                            message.channel.send(f"Failed to send autoresponder '{ar_name}' in guild {guild_id}: Bot lacks permissions")
                            break

                    for emoji in reactions:
                        try:
                            await message.add_reaction(emoji)
                        except discord.HTTPException:
                            print(f"Failed to add reaction '{emoji}' for autoresponder '{ar_name}'")

                break

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        lang = cfg.get_user_config(user.id, "language") or "en"
        if reaction.message.id in self.ar_messages:
            ar_info = self.ar_messages[reaction.message.id]

            if str(reaction.emoji) == "🗑️":
                await reaction.message.delete()
                del self.ar_messages[reaction.message.id]

            elif str(reaction.emoji) == "❓":
                embed = discord.Embed(
                    title=localization.get("config", "ar.info", lang=lang, name=ar_info["name"]),
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name=localization.get("config", "ar.name", lang=lang),
                    value=ar_info["name"],
                    inline=False,
                )
                embed.add_field(
                    name=localization.get("config", "ar.trigger", lang=lang),
                    value=ar_info["trigger"],
                    inline=False,
                )
                embed.add_field(
                    name=localization.get("config", "ar.creator", lang=lang),
                    value=f"<@{ar_info['creator_id']}>",
                    inline=False,
                )

                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.group(name="autoresponder", aliases=["ar"], invoke_without_command=True)
    async def autoresponder(self, ctx):
        """Command group for autoresponders"""
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        pfx = cfg.get_guild_config(ctx.guild.id, "prefix") or "y;"

        embed = discord.Embed(
            title=localization.get("config", "ar.title", lang=lang),
            description=localization.get("config", "ar.description", lang=lang),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name=localization.get("config", "ar.create", lang=lang),
            value=f"{pfx}{localization.get('config', 'ar.cmds.create', lang=lang)}",
            inline=False,
        )
        embed.add_field(
            name=localization.get("config", "ar.edit", lang=lang),
            value=f"{pfx}{localization.get('config', 'ar.cmds.edit', lang=lang)}",
            inline=False,
        )
        embed.add_field(
            name=localization.get("config", "ar.delete", lang=lang),
            value=f"{pfx}{localization.get('config', 'ar.cmds.delete', lang=lang)}",
            inline=False,
        )
        embed.add_field(
            name=localization.get("config", "ar.list", lang=lang),
            value=f"{pfx}{localization.get('config', 'ar.cmds.list', lang=lang)}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @autoresponder.command(name="create")
    @commands.has_permissions(manage_guild=True)
    async def ar_create(
        self, ctx, name: str, trigger: str, response: str, language: str = "en"
    ):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"

        if autoresponder_exists(guild_id, name):
            await ctx.send(localization.get("config", "ar.already_exists", lang=lang, name=name))
            return

        allowed, error = self.check_restricted_placeholders(response, ctx.author)
        if not allowed:
            await ctx.send(error)
            return

        create_autoresponder(guild_id, name, trigger, response, str(ctx.author.id), language)

        embed = discord.Embed(
            title=localization.get("config", "ar.create_success", lang=lang, name=name),
            color=discord.Color.green(),
        )
        embed.add_field(
            name=localization.get("config", "ar.name", lang=lang),
            value=name,
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.trigger", lang=lang),
            value=trigger,
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.language", lang=lang),
            value=language,
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.response", lang=lang),
            value=response[:1000] + "..." if len(response) > 1000 else response,
            inline=False,
        )

        await ctx.send(embed=embed)

    @autoresponder.command(name="edit")
    async def ar_edit(self, ctx, name: str, response: str, language: str = "en"):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"

        if not autoresponder_exists(guild_id, name):
            await ctx.send(localization.get("config", "ar.not_found", lang=lang, name=name))
            return

        ar_data = get_autoresponder(guild_id, name, language) or get_autoresponder(guild_id, name, "en")
        if not ar_data:
            await ctx.send(localization.get("config", "ar.not_found", lang=lang, name=name))
            return

        if not ctx.author.guild_permissions.manage_guild and str(ctx.author.id) != ar_data["creator_id"]:
            await ctx.send(localization.get("config", "ar.no_permission", lang=lang))
            return

        allowed, error = self.check_restricted_placeholders(response, ctx.author)
        if not allowed:
            await ctx.send(error)
            return

        if update_autoresponder(guild_id, name, response, language):
            embed = discord.Embed(
                title=localization.get("config", "ar.edit_success", lang=lang, name=name),
                color=discord.Color.blue(),
            )
            embed.add_field(
                name=localization.get("config", "ar.name", lang=lang),
                value=name,
                inline=True
            )
            embed.add_field(
                name=localization.get("config", "ar.language", lang=lang),
                value=language,
                inline=True
            )
            embed.add_field(
                name=localization.get("config", "ar.response", lang=lang),
                value=response[:1000] + "..." if len(response) > 1000 else response,
                inline=False,
            )

            await ctx.send(embed=embed)
        else:
            create_autoresponder(
                guild_id,
                name,
                ar_data["trigger"],
                response,
                ar_data["creator_id"],
                language,
            )
            embed = discord.Embed(
                title=localization.get("config", "ar.language_added", lang=language, name=name),
                color=discord.Color.green(),
            )
            embed.add_field(
                name=localization.get("config", "ar.name", lang=lang),
                value=name,
                inline=True
            )
            embed.add_field(
                name=localization.get("config", "ar.language", lang=lang),
                value=language,
                inline=True
            )
            embed.add_field(
                name=localization.get("config", "ar.response", lang=lang),
                value=response[:1000] + "..." if len(response) > 1000 else response,
                inline=False,
            )
            await ctx.send(embed=embed)

    @autoresponder.command(name="delete")
    @commands.has_permissions(manage_guild=True)
    async def ar_delete(self, ctx, name: str):
        """Delete an autoresponder"""
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"

        if delete_autoresponder(guild_id, name):
            await ctx.send(localization.get("config", "ar.delete_success", lang=lang, name=name))
        else:
            await ctx.send(localization.get("config", "ar.not_found", lang=lang, name=name))

    @autoresponder.command(name="list")
    async def ar_list(self, ctx):
        guild_id = str(ctx.guild.id)
        autoresponders = get_all_autoresponders(guild_id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"

        if not autoresponders:
            await ctx.send(localization.get("config", "ar.no_autoresponders", lang=lang))
            return

        embed = discord.Embed(
            title=localization.get("config", "ar.list_success", lang=lang, guild=ctx.guild.name),
            color=discord.Color.blue(),
        )

        grouped = {}
        for ar in autoresponders:
            name = ar["name"]
            if name not in grouped:
                grouped[name] = {"trigger": ar["trigger"], "languages": []}
            grouped[name]["languages"].append(ar["language"])

        for name, data in grouped.items():
            languages = ", ".join(data["languages"])
            embed.add_field(
                name=name,
                value=f"{localization.get('config', 'ar.trigger', lang=lang)}: `{data['trigger']}`\n{localization.get('config', 'ar.language', lang=lang)}: {languages}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @ar_create.error
    @ar_edit.error
    @ar_delete.error
    async def ar_error(self, ctx, error):
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(localization.get("config", "ar.argument_missing", lang=lang, arg=error.param.name))
        elif isinstance(error, commands.BadArgument):
            await ctx.send(localization.get("config", "ar.invalid_name", lang=lang))
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(localization.get("config", "ar.no_permission", lang=lang))
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(localization.get("config", "ar.failure", lang=lang))

async def setup(bot):
    await bot.add_cog(AutoresponderCog(bot))