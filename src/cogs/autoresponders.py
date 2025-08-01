import discord
from discord.ext import commands
import sqlite3
from typing import Optional, List

from src.utils.localization import localization
from src.utils.placeholders import pl
import src.utils.config as cfg

DB_PATH = "config.db"


def create_autoresponder(
    guild_id: str,
    name: str,
    trigger: str,
    response: str,
    creator_id: str,
    language: str = "en",
):
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO autoresponders 
            (guild_id, name, trigger, response, language, creator_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """,
            (guild_id, name, trigger, response, language, creator_id),
        )
        conn.commit()


def get_autoresponder(guild_id: str, name: str, language: str = "en") -> Optional[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT trigger, response, creator_id 
            FROM autoresponders 
            WHERE guild_id = ? AND name = ? AND language = ?
        """,
            (guild_id, name, language),
        )
        row = c.fetchone()
        if row:
            return {"trigger": row[0], "response": row[1], "creator_id": row[2]}
        return None


def get_all_autoresponders(guild_id: str) -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT name, trigger, response, language, creator_id
            FROM autoresponders 
            WHERE guild_id = ?
            ORDER BY name, language
        """,
            (guild_id,),
        )
        rows = c.fetchall()
        return [
            {
                "name": row[0],
                "trigger": row[1],
                "response": row[2],
                "language": row[3],
                "creator_id": row[4],
            }
            for row in rows
        ]


def get_guild_triggers(guild_id: str) -> List[dict]:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT name, trigger, response, language, creator_id
            FROM autoresponders 
            WHERE guild_id = ?
        """,
            (guild_id,),
        )
        rows = c.fetchall()
        return [
            {
                "name": row[0],
                "trigger": row[1],
                "response": row[2],
                "language": row[3],
                "creator_id": row[4],
            }
            for row in rows
        ]


def update_autoresponder(guild_id: str, name: str, response: str, language: str = "en"):
    """update an existing autoresponder response"""
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            UPDATE autoresponders 
            SET response = ?
            WHERE guild_id = ? AND name = ? AND language = ?
        """,
            (response, guild_id, name, language),
        )
        conn.commit()
        return c.rowcount > 0


def delete_autoresponder(guild_id: str, name: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            DELETE FROM autoresponders 
            WHERE guild_id = ? AND name = ?
        """,
            (guild_id, name),
        )
        conn.commit()
        return c.rowcount > 0


def autoresponder_exists(guild_id: str, name: str) -> bool:
    with sqlite3.connect(DB_PATH) as conn:
        c = conn.cursor()
        c.execute(
            """
            SELECT 1 FROM autoresponders 
            WHERE guild_id = ? AND name = ? LIMIT 1
        """,
            (guild_id, name),
        )
        return c.fetchone() is not None


class AutoresponderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ar_messages = {}

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot:
            return

        if not message.guild:
            return

        guild_id = str(message.guild.id)
        triggers = get_guild_triggers(guild_id)

        for ar_data in triggers:
            trigger = ar_data["trigger"].lower()
            content = message.content.lower()

            if trigger in content:
                response = ar_data["response"]

                if response:
                    processed_response, reactions = await pl(
                        message, response
                    )

                    if processed_response:
                        sent_message = await message.channel.send(processed_response)
                        self.ar_messages[sent_message.id] = {
                            "name": ar_data["name"],
                            "creator_id": ar_data["creator_id"],
                            "trigger": ar_data["trigger"],
                        }

                    for emoji in reactions:
                        try:
                            await message.add_reaction(emoji)
                        except discord.HTTPException:
                            pass

                break

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.bot:
            return

        lang = cfg.get_user_config(user.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        if reaction.message.id in self.ar_messages:
            ar_info = self.ar_messages[reaction.message.id]

            if str(reaction.emoji) in ["❌", "🗑️"]:
                await reaction.message.delete()
                del self.ar_messages[reaction.message.id]

            elif str(reaction.emoji) == "❓":
                embed = discord.Embed(
                    title=armsg.get("info", "Autoresponder info").format(name=ar_info["name"]).format(
                        name=ar_info["name"]
                    ),
                    color=discord.Color.blue(),
                )
                embed.add_field(
                    name=armsg.get("name", "Name"),
                    value=ar_info["name"],
                    inline=False,
                )
                embed.add_field(
                    name=armsg.get("trigger", "Trigger"),
                    value=ar_info["trigger"],
                    inline=False,
                )
                embed.add_field(
                    name=armsg.get("creator", "Creator"),
                    value=f"<@{ar_info['creator_id']}>",
                    inline=False,
                )

                try:
                    await user.send(embed=embed)
                except discord.Forbidden:
                    pass

    @commands.group(name="autoresponder", aliases=["ar"], invoke_without_command=True)
    async def autoresponder(self, ctx):
        """command group for autoresponders"""
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        pfx = cfg.get_guild_config(ctx.guild.id, "prefix") or "y;"

        embed = discord.Embed(
            title=armsg.get("title", "Autoresponders"),
            description=armsg.get("description", "Manage your autoresponders here."),
            color=discord.Color.blue(),
        )
        embed.add_field(
            name=armsg.get("create", "Create"),
            value=f"{pfx}{armsg.get('cmds', {}).get('create', 'ar create <name> "<trigger>" "<response>" [language]')}",
            inline=False,
        )
        embed.add_field(
            name=armsg.get("edit", "Edit"),
            value=f"{pfx}{armsg.get('cmds', {}).get('edit', 'ar edit <name> "<response>" [language]')}",
            inline=False,
        )
        embed.add_field(
            name=armsg.get("delete", "Delete"),
            value=f"{pfx}{armsg.get('cmds', {}).get('delete', 'ar delete <name>')}",
            inline=False,
        )
        embed.add_field(
            name=armsg.get("list"),
            value=f"{pfx}{armsg.get('cmds', {}).get('list', 'ar list')}",
            inline=False,
        )
        await ctx.send(embed=embed)

    @autoresponder.command(name="create")
    async def ar_create(
        self, ctx, name: str, trigger: str, response: str, language: str = "en"
    ):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        if autoresponder_exists(guild_id, name):
            await ctx.send(
                armsg.get(
                    "already_exists", "Autoresponder {name} already exists."
                ).format(name=name)
            )
            return

        create_autoresponder(
            guild_id, name, trigger, response, str(ctx.author.id), language
        )

        embed = discord.Embed(
            title=armsg.get("create_success", "Autoresponder created.").format(
                name=name
            ),
            color=discord.Color.green(),
        )
        embed.add_field(name=armsg.get("name", "Name"), value=name, inline=True)
        embed.add_field(
            name=armsg.get("trigger", "Trigger"), value=trigger, inline=True
        )
        embed.add_field(
            name=armsg.get("language", "Language"), value=language, inline=True
        )
        embed.add_field(
            name=armsg.get("response", "Response"),
            value=response[:1000] + "..." if len(response) > 1000 else response,
            inline=False,
        )

        await ctx.send(embed=embed)

    @autoresponder.command(name="edit")
    async def ar_edit(self, ctx, name: str, response: str, language: str = "en"):
        guild_id = str(ctx.guild.id)

        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        if not autoresponder_exists(guild_id, name):
            await ctx.send(
                armsg.get("not_found", "{name} not found.").format(name=name)
            )
            return

        if update_autoresponder(guild_id, name, response, language):
            embed = discord.Embed(
                title=armsg.get("edit_success", "{name} modified.").format(name=name),
                color=discord.Color.blue(),
            )
            embed.add_field(name=armsg.get("name", "Name"), value=name, inline=True)
            embed.add_field(
                name=armsg.get("language", "Language"), value=language, inline=True
            )
            embed.add_field(
                name=armsg.get("response", "Response"),
                value=response[:1000] + "..." if len(response) > 1000 else response,
                inline=False,
            )

            await ctx.send(embed=embed)
        else:
            ar_data = get_autoresponder(guild_id, name, "en")
            if ar_data:
                create_autoresponder(
                    guild_id,
                    name,
                    ar_data["trigger"],
                    response,
                    ar_data["creator_id"],
                    language,
                )
                embed = discord.Embed(
                    title=armsg.get("language_added", "Added {lang}.").format(
                        lang=language
                    ),
                    color=discord.Color.green(),
                )
                embed.add_field(name=armsg.get("name", "Name"), value=name, inline=True)
                embed.add_field(
                    name=armsg.get("language", "Language"), value=language, inline=True
                )
                embed.add_field(
                    name=armsg.get("response", "Response"),
                    value=response[:1000] + "..." if len(response) > 1000 else response,
                    inline=False,
                )
                await ctx.send(embed=embed)

    @autoresponder.command(name="delete")
    async def ar_delete(self, ctx, name: str):
        """Delete an autoresponder"""
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        if delete_autoresponder(guild_id, name):
            await ctx.send(
                armsg.get("delete_success", "Autoresponder {name} deleted.").format(
                    name=name
                )
            )
        else:
            await ctx.send(
                armsg.get("not_found", "{name} not found.").format(name=name)
            )

    @autoresponder.command(name="list")
    async def ar_list(self, ctx):
        guild_id = str(ctx.guild.id)
        autoresponders = get_all_autoresponders(guild_id)

        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})

        if not autoresponders:
            await ctx.send(
                armsg.get(
                    "no_autoresponders", "No autoresponders found in this server."
                )
            )
            return

        embed = discord.Embed(
            title=armsg.get("list_success", "Autoresponders in this server:").format(
                guild=ctx.guild.name
            ),
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
                value=f"{armsg.get('trigger', 'Trigger')}: `{data['trigger']}`\n{armsg.get('language', 'Languages')}: {languages}",
                inline=False,
            )

        await ctx.send(embed=embed)

    @ar_create.error
    @ar_edit.error
    @ar_delete.error
    async def ar_error(self, ctx, error):
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        msg = localization.languages.get(lang, {}).get("config", {})
        armsg = msg.get("ar", {})
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(
                armsg.get(
                    "argument_missing", "Missing required argument `{arg}`."
                ).format(arg=error.param.name)
            )
        elif isinstance(error, commands.BadArgument):
            await ctx.send(
                armsg.get(
                    "invalid_name",
                    "Invalid autoresponder name. It must be alphanumeric, and spaces aren't allowed.",
                )
            )
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(
                armsg.get(
                    "failure", "Failed to perform the action. Something went wrong."
                )
            )


async def setup(bot):
    await bot.add_cog(AutoresponderCog(bot))
