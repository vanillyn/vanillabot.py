import discord
from discord.ext import commands
from datetime import timedelta
from src.utils.localization import localization
import src.utils.config as config


class Moderation(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="warn")
    @commands.has_permissions(manage_messages=True)
    async def warn(self, ctx, member: discord.Member, *, reason=None):
        """issues a warning"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        warn = messages.get("warn")

        if not reason:
            ctx.send(warn.get("no_reason", "[lang error] No reason provided."))
            return

        if not member:
            ctx.send(warn.get("no_user", "[lang error] No user specified."))
            return
        try:
            config.add_infraction(
                ctx.guild.id, member.id, "warn", reason, None, ctx.author.id
            )
            await member.send(
                warn.get(
                    "message", "[lang error] You have been warned. Reason: {reason}"
                ).format(reason=reason)
            )
        except discord.Forbidden:
            await ctx.send(
                warn.get(
                    "message_failed",
                    "[lang error] Failed to send warning message to {user}.",
                ).format(user=member.mention)
            )
            return

        await ctx.send(
            warn.get("success", "[lang error] User {user} has been warned.").format(
                user=member.mention, reason=reason
            )
        )

    @commands.command(name="note")
    @commands.has_permissions(manage_guild=True)
    async def note(
        self,
        ctx,
        public_or_member: str,
        maybe_member: discord.Member = None,
        *,
        note=None,
    ):
        """adds a note to a user"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        notem = messages.get("note", {})

        public = False
        member = None

        if public_or_member.lower() == "public":
            public = True
            member = maybe_member
        else:
            member = ctx.message.mentions[0] if ctx.message.mentions else None
            note = f"{maybe_member} {note}".strip() if maybe_member else note

        if not note:
            await ctx.send(notem.get("no_note", "[lang error] No note provided."))
            return

        if not member:
            await ctx.send(notem.get("no_user", "[lang error] No user specified."))
            return

        if public:
            await ctx.send("global notes arent implemented yet.")
            # config.add_note(member.id, note, ctx.author.id)
        else:
            config.add_infraction(
                ctx.guild.id, member.id, "note", note, None, ctx.author.id
            )

        await ctx.send(
            notem.get("success_local", "[lang error] Note added for {user}.").format(
                user=member.mention, note=note
            )
        )

    @commands.command(name="ban")
    @commands.has_permissions(ban_members=True)
    async def ban(
        self, ctx, member: discord.Member, duration: str = None, *, reason=None
    ):
        """bans a user"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        ban_msg = messages.get("ban", {})

        if not reason:
            reason = ban_msg.get("no_reason", "[lang error] No reason provided.")

        delta = None
        if duration:
            try:
                unit = duration[-1]
                num = int(duration[:-1])
                if unit == "h":
                    delta = timedelta(hours=num)
                elif unit == "d":
                    delta = timedelta(days=num)
                elif unit == "m":
                    delta = timedelta(minutes=num)
                else:
                    raise ValueError()
            except (ValueError, IndexError):
                await ctx.send(
                    ban_msg.get(
                        "invalid_duration",
                        "[lang error] Invalid duration format. Use '1h', '1d', or '1m'.",
                    )
                )
                return

        try:
            try:
                await member.send(
                    ban_msg.get(
                        "message",
                        "[lang error] You have been banned from {guild}{for_duration}. Reason: {reason}",
                    ).format(
                        guild=ctx.guild.name,
                        for_duration=f" for {delta}" if duration else "",
                        reason=reason,
                    )
                )
            except discord.Forbidden:
                await ctx.send(
                    ban_msg.get(
                        "message_failed",
                        "[lang error] Failed to send ban message to {user}.",
                    ).format(user=member.mention)
                )
                return
            await member.ban(reason=reason)
            config.add_infraction(
                ctx.guild.id, member.id, "ban", reason, delta, ctx.author.id
            )
            await ctx.send(
                ban_msg.get(
                    "success", "[lang error] User {user} has been banned."
                ).format(
                    user=member.mention,
                    user_id=member.id,
                    for_duration=f" for {delta}" if duration else "",
                    reason=reason,
                )
            )
        except discord.Forbidden:
            await ctx.send(
                ban_msg.get(
                    "no_permission",
                    "[lang error] You do not have permission to ban users.",
                )
            )
        except Exception as e:
            await ctx.send(
                ban_msg.get(
                    "failure", "[lang error] Failed to ban user {user}."
                ).format(user=member.mention)
            )
            print(f"Error banning user: {e}")

    @commands.command(name="kick")
    @commands.has_permissions(kick_members=True)
    async def kick(self, ctx, member: discord.Member, *, reason=None):
        """kicks a user"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        kick_msg = messages.get("kick", {})

        if not reason:
            reason = kick_msg.get("no_reason", "[lang error] No reason provided.")

        try:
            try:
                await member.send(
                    kick_msg.get(
                        "message",
                        "[lang error] You have been kicked from {guild}. Reason: {reason}",
                    ).format(guild=ctx.guild.name, reason=reason)
                )
            except discord.Forbidden:
                await ctx.send(
                    kick_msg.get(
                        "message_failed",
                        "[lang error] Failed to send kick message to {user}.",
                    ).format(user=member.mention)
                )
            await member.kick(reason=reason)
            config.add_infraction(
                ctx.guild.id, member.id, "kick", reason, None, ctx.author.id
            )
            await ctx.send(
                kick_msg.get(
                    "success", "[lang error] User {user} has been kicked."
                ).format(user=member.mention, user_id=member.id, reason=reason)
            )
        except discord.Forbidden:
            await ctx.send(
                kick_msg.get(
                    "no_permission",
                    "[lang error] You do not have permission to kick users.",
                )
            )
        except Exception as e:
            await ctx.send(
                kick_msg.get(
                    "failure", "[lang error] Failed to kick user {user}."
                ).format(user=member.mention)
            )
            print(f"Error kicking user: {e}")

    @commands.command(name="unban")
    @commands.has_permissions(ban_members=True)
    async def unban(self, ctx, user_id: int, *, reason=None):
        """unbans a user"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        unban_msg = messages.get("unban", {})

        if not reason:
            reason = unban_msg.get("no_reason", "[lang error] No reason provided.")

        try:
            user = await self.bot.fetch_user(user_id)
            if ctx.guild.get_member(user.id):
                await ctx.send(
                    unban_msg.get("not_banned", "[lang error] User is not banned."),
                    format(user=user.mention),
                )
                return

            await ctx.guild.unban(user, reason=reason)
            config.add_infraction(
                ctx.guild.id, user.id, "unban", reason, None, ctx.author.id
            )
            await ctx.send(
                unban_msg.get(
                    "success", "[lang error] User {user} has been unbanned."
                ).format(user=user.mention, user_id=user.id, reason=reason)
            )
        except discord.NotFound:
            await ctx.send(unban_msg.get("not_found", "[lang error] User not found."))
        except discord.Forbidden:
            await ctx.send(
                unban_msg.get(
                    "no_permission",
                    "[lang error] You do not have permission to unban users.",
                )
            )
        except Exception as e:
            await ctx.send(
                unban_msg.get(
                    "failure", "[lang error] Failed to unban user {user}."
                ).format(user=user.mention)
            )
            print(f"Error unbanning user: {e}")

    @commands.command(name="info")
    async def info(self, ctx, member: discord.Member = None):
        """shows information about a user"""
        if not member:
            member = ctx.author

        # lang = config.get_language(ctx.author.id, ctx.guild.id)
        # messages = localization.languages.get(lang, {}).get("moderation", {})
        # info_msg = messages.get("info", {})

        embed = discord.Embed(
            title=f"User Info: {member.name}", color=discord.Color.blue()
        )
        embed.add_field(name="ID", value=member.id, inline=False)
        embed.add_field(
            name="Joined at",
            value=member.joined_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False,
        )
        embed.add_field(
            name="Created at",
            value=member.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            inline=False,
        )

        infractions = config.get_infractions(ctx.guild.id, member.id)

        if infractions:
            infraction_list = "\n".join(
                [f"{inf[2]} | {inf[0]} by <@{inf[4]}>: {inf[1]}" for inf in infractions]
            )
            embed.add_field(name="Infractions", value=infraction_list, inline=False)
        else:
            embed.add_field(
                name="Infractions", value="No infractions found.", inline=False
            )

        notes = config.get_notes(member.id)
        if notes:
            note_list = "\n".join(
                [f"{note[0]} (by <@{note[1]}> on {note[2]})" for note in notes]
            )
            embed.add_field(name="Notes", value=note_list, inline=False)
        else:
            embed.add_field(name="Notes", value="No notes found.", inline=False)

        await ctx.send(embed=embed)

    @commands.command(name="timeout")
    @commands.has_permissions(moderate_members=True)
    async def timeout(self, ctx, member: discord.Member, duration: str, *, reason=None):
        """times out a user"""
        lang = config.get_language(ctx.author.id, ctx.guild.id)
        messages = localization.languages.get(lang, {}).get("moderation", {})
        timeout_msg = messages.get("timeout", {})

        if not reason:
            reason = timeout_msg.get("no_reason", "[lang error] No reason provided.")

        delta = None
        if duration:
            try:
                unit = duration[-1]
                num = int(duration[:-1])
                if unit == "h":
                    delta = timedelta(hours=num)
                elif unit == "d":
                    delta = timedelta(days=num)
                elif unit == "m":
                    delta = timedelta(minutes=num)
                else:
                    raise ValueError()
            except (ValueError, IndexError):
                await ctx.send(
                    timeout_msg.get(
                        "invalid_duration",
                        "[lang error] Invalid duration format. Use '1h', '1d', or '1m'.",
                    )
                )
                return

        try:
            try:
                await member.send(
                    timeout_msg.get(
                        "message",
                        "[lang error] You have been put in timeout for {duration}. Reason: {reason}",
                    ).format(duration=delta, reason=reason)
                )
            except discord.Forbidden:
                await ctx.send(
                    timeout_msg.get(
                        "message_failed",
                        "[lang error] Failed to send timeout message to {user}.",
                    ).format(user=member.mention)
                )

            await member.timeout(delta, reason=reason)
            await ctx.send(
                timeout_msg.get(
                    "success", "[lang error] User {user} has been timed out."
                ).format(
                    user=member.mention,
                    user_id=member.id,
                    duration=delta,
                    reason=reason,
                )
            )
        except discord.Forbidden:
            await ctx.send(
                timeout_msg.get(
                    "no_permission",
                    "[lang error] You do not have permission to timeout users.",
                )
            )
        except Exception as e:
            await ctx.send(
                timeout_msg.get(
                    "failure", "[lang error] Failed to timeout user {user}."
                ).format(user=member.mention)
            )
            print(f"Error timing out user: {e}")


async def setup(bot):
    await bot.add_cog(Moderation(bot))
