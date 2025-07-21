import discord
from discord.ext import commands
from src.utils.localization import localization
import src.utils.config as config

class Moderation(commands.Cog):
	def __init__(self, bot):
		self.bot = bot

	@commands.command()
	@commands.has_permissions(ban_members=True)
	async def ban(self, ctx, member: discord.Member = None, *, reason=None):
		lang = await config.get_language(ctx.guild.id)
		if not member:
			return await ctx.send(localization.get("mod.fail.no_target", lang=lang))
		if not reason:
			return await ctx.send(localization.get("mod.fail.no_reason", lang=lang))
		
		await member.ban(reason=reason)
		await ctx.send(localization.get("mod.ban.success", lang=lang, user=member.mention, reason=reason))

		log_channel = await config.get_log_channel(ctx.guild.id)
		if log_channel:
			text = localization.get("log.user_banned", lang=lang, moderator=ctx.author.mention, user=member.mention, reason=reason)
			await log_channel.send(text)

	@commands.command()
	@commands.has_permissions(kick_members=True)
	async def kick(self, ctx, member: discord.Member = None, *, reason=None):
		lang = await config.get_language(ctx.guild.id)
		if not member:
			return await ctx.send(localization.get("mod.fail.no_target", lang=lang))
		if not reason:
			return await ctx.send(localization.get("mod.fail.no_reason", lang=lang))
		
		await member.kick(reason=reason)
		await ctx.send(localization.get("mod.kick.success", lang=lang, user=member.mention, reason=reason))

		log_channel = await config.get_log_channel(ctx.guild.id)
		if log_channel:
			text = localization.get("log.user_kicked", lang=lang, moderator=ctx.author.mention, user=member.mention, reason=reason)
			await log_channel.send(text)

	@commands.command()
	@commands.has_permissions(ban_members=True)
	async def unban(self, ctx, user_id: int):
		lang = await config.get_language(ctx.guild.id)
		user = await self.bot.fetch_user(user_id)
		await ctx.guild.unban(user)
		await ctx.send(localization.get("mod.unban.success", lang=lang, user=user.mention))

		log_channel = await config.get_log_channel(ctx.guild.id)
		if log_channel:
			text = localization.get("log.user_unbanned", lang=lang, moderator=ctx.author.mention, user=user.mention)
			await log_channel.send(text)

async def setup(bot):
	await bot.add_cog(Moderation(bot))
