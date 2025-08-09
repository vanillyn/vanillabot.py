import discord
from discord.ext import commands
import asyncio
import re
from src.utils.localization import localization
from src.utils.placeholders import pl
from src.utils.config.utils import get_guild_triggers, get_all_autoresponders, get_autoresponder, create_autoresponder, update_autoresponder, delete_autoresponder, autoresponder_exists
import src.utils.config.utils as cfg

class edit_view(discord.ui.View):
    def __init__(self, bot, ar_data, user_id, guild_id, language):
        super().__init__(timeout=300)
        self.bot = bot
        self.ar_data = ar_data
        self.user_id = user_id
        self.guild_id = guild_id
        self.language = language

    async def check_permissions(self, user, action):
        ar_data = self.ar_data
        guild = self.bot.get_guild(int(self.guild_id))
        edit_role = cfg.get_guild_config(self.guild_id, 'autoresponder_edit_role')
        edit_perm = cfg.get_guild_config(self.guild_id, 'autoresponder_edit_permission')
        editor_role = ar_data.get('editor_role')
        editors = ar_data.get('editors', '').split(',') if ar_data.get('editors') else []
        permissions = ar_data.get('edit_permissions', '').split(',') if ar_data.get('edit_permissions') else []

        if str(user.id) == ar_data['creator_id']:
            return True
        if edit_role and any(role.id == edit_role for role in user.roles):
            return True
        if getattr(user.guild_permissions, edit_perm, False):
            return True
        if editor_role and (editor_role == guild.default_role.id or any(role.id == editor_role for role in user.roles)):
            return action in permissions
        if str(user.id) in editors:
            return action in permissions
        return False

    @discord.ui.button(label="Edit Trigger", style=discord.ButtonStyle.primary)
    async def edit_trigger(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction.user, 'edit'):
            lang = cfg.get_user_config(interaction.user.id, "language") or "en"
            await interaction.response.send_message(localization.get("config", "ar.no_edit_permission", lang=lang, action="edit trigger"), ephemeral=True)
            return
        lang = cfg.get_user_config(interaction.user.id, "language") or "en"
        await interaction.response.send_message(
            localization.get("config", "ar.edit_prompt_trigger", lang=lang, trigger=self.ar_data['trigger']),
            ephemeral=True
        )
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "ar.cancel", lang=lang), ephemeral=True)
                return
            if re.search(r"\{[^}]*\}", msg.content):
                await interaction.followup.send(localization.get("config", "ar.invalid_trigger", lang=lang), ephemeral=True)
                return
            update_autoresponder(self.guild_id, self.ar_data['name'], self.language, trigger=msg.content)
            self.ar_data['trigger'] = msg.content
            await interaction.followup.send(localization.get("config", "ar.edit_success", lang=lang, name=self.ar_data['name']), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "ar.timeout", lang=lang), ephemeral=True)

    @discord.ui.button(label="Edit Response", style=discord.ButtonStyle.primary)
    async def edit_response(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction.user, 'edit'):
            lang = cfg.get_user_config(interaction.user.id, "language") or "en"
            await interaction.response.send_message(localization.get("config", "ar.no_edit_permission", lang=lang, action="edit response"), ephemeral=True)
            return
        lang = cfg.get_user_config(interaction.user.id, "language") or "en"
        preview = self.ar_data['response'][:100] + "..." if len(self.ar_data['response']) > 100 else self.ar_data['response']
        await interaction.response.send_message(
            localization.get("config", "ar.edit_prompt_response", lang=lang, response=preview),
            ephemeral=True
        )
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "ar.cancel", lang=lang), ephemeral=True)
                return
            allowed, error = self.bot.get_cog('AutoresponderCog').check_restricted_placeholders(msg.content, interaction.user)
            if not allowed:
                await interaction.followup.send(error, ephemeral=True)
                return
            update_autoresponder(self.guild_id, self.ar_data['name'], self.language, response=msg.content)
            self.ar_data['response'] = msg.content
            if str(interaction.user.id) not in self.ar_data.get('contributors', '').split(','):
                contributors = self.ar_data.get('contributors', '').split(',') + [str(interaction.user.id)]
                update_autoresponder(self.guild_id, self.ar_data['name'], self.language, contributors=','.join(filter(None, contributors)))
                self.ar_data['contributors'] = ','.join(filter(None, contributors))
            await interaction.followup.send(localization.get("config", "ar.edit_success", lang=lang, name=self.ar_data['name']), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "ar.timeout", lang=lang), ephemeral=True)

    @discord.ui.button(label="Edit Arguments", style=discord.ButtonStyle.primary)
    async def edit_arguments(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction.user, 'edit'):
            lang = cfg.get_user_config(interaction.user.id, "language") or "en"
            await interaction.response.send_message(localization.get("config", "ar.no_edit_permission", lang=lang, action="edit arguments"), ephemeral=True)
            return
        lang = cfg.get_user_config(interaction.user.id, "language") or "en"
        await interaction.response.send_message(
            localization.get("config", "ar.edit_prompt_arguments", lang=lang, arguments=self.ar_data['arguments']),
            ephemeral=True
        )
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "ar.cancel", lang=lang), ephemeral=True)
                return
            if msg.content not in ['none', 'user']:
                await interaction.followup.send(localization.get("config", "ar.invalid_arguments", lang=lang), ephemeral=True)
                return
            update_autoresponder(self.guild_id, self.ar_data['name'], self.language, arguments=msg.content)
            self.ar_data['arguments'] = msg.content
            await interaction.followup.send(localization.get("config", "ar.edit_success", lang=lang, name=self.ar_data['name']), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "ar.timeout", lang=lang), ephemeral=True)

    @discord.ui.button(label="Edit Editors", style=discord.ButtonStyle.primary)
    async def edit_editors(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction.user, 'add_editors'):
            lang = cfg.get_user_config(interaction.user.id, "language") or "en"
            await interaction.response.send_message(localization.get("config", "ar.no_edit_permission", lang=lang, action="add editors"), ephemeral=True)
            return
        lang = cfg.get_user_config(interaction.user.id, "language") or "en"
        editors = self.ar_data.get('editors', '') or 'None'
        await interaction.response.send_message(
            localization.get("config", "ar.edit_prompt_editors", lang=lang, editors=editors),
            ephemeral=True
        )
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "ar.cancel", lang=lang), ephemeral=True)
                return
            editors = self.ar_data.get('editors', '').split(',') if self.ar_data.get('editors') else []
            editors = set(filter(None, editors))
            for part in msg.content.split(','):
                if part.startswith('+') and part[1:].isdigit():
                    editors.add(part[1:])
                elif part.startswith('-') and part[1:] in editors:
                    editors.remove(part[1:])
                else:
                    await interaction.followup.send(localization.get("config", "ar.invalid_editors", lang=lang), ephemeral=True)
                    return
            update_autoresponder(self.guild_id, self.ar_data['name'], self.language, editors=','.join(editors))
            self.ar_data['editors'] = ','.join(editors)
            await interaction.followup.send(localization.get("config", "ar.edit_success", lang=lang, name=self.ar_data['name']), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "ar.timeout", lang=lang), ephemeral=True)

    @discord.ui.button(label="Edit Permissions", style=discord.ButtonStyle.primary)
    async def edit_permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self.check_permissions(interaction.user, 'add_editors'):
            lang = cfg.get_user_config(interaction.user.id, "language") or "en"
            await interaction.response.send_message(localization.get("config", "ar.no_edit_permission", lang=lang, action="edit permissions"), ephemeral=True)
            return
        lang = cfg.get_user_config(interaction.user.id, "language") or "en"
        permissions = self.ar_data.get('edit_permissions', '') or 'None'
        await interaction.response.send_message(
            localization.get("config", "ar.edit_prompt_permissions", lang=lang, permissions=permissions),
            ephemeral=True
        )
        try:
            msg = await self.bot.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "ar.cancel", lang=lang), ephemeral=True)
                return
            valid_perms = {'edit', 'delete', 'add_language', 'edit_non_default', 'add_editors'}
            new_perms = set(msg.content.split(','))
            if not new_perms.issubset(valid_perms):
                await interaction.followup.send(localization.get("config", "ar.invalid_permissions", lang=lang), ephemeral=True)
                return
            update_autoresponder(self.guild_id, self.ar_data['name'], self.language, edit_permissions=','.join(new_perms))
            self.ar_data['edit_permissions'] = ','.join(new_perms)
            await interaction.followup.send(localization.get("config", "ar.edit_success", lang=lang, name=self.ar_data['name']), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "ar.timeout", lang=lang), ephemeral=True)

    async def create_edit_embed(self, user):
        lang = cfg.get_language(user.id, self.guild_id) or "en"
        preview = self.ar_data['response'][:100] + "..." if len(self.ar_data['response']) > 100 else self.ar_data['response']
        embed = discord.Embed(
            title=localization.get("config", "ar.info", lang=lang, name=self.ar_data['name']),
            color=discord.Color.blue()
        )
        embed.add_field(
            name=localization.get("config", "ar.name", lang=lang),
            value=self.ar_data['name'],
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.trigger", lang=lang),
            value=self.ar_data['trigger'],
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.preview_response", lang=lang),
            value=preview,
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "ar.language", lang=lang),
            value=self.ar_data['language'],
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.creator", lang=lang),
            value=f"<@{self.ar_data['creator_id']}>",
            inline=True
        )
        editors = self.ar_data.get('editors', '') or 'None'
        editors = ', '.join(f"<@{e}>" for e in editors.split(',') if e) if editors != 'None' else 'None'
        embed.add_field(
            name=localization.get("config", "ar.editors", lang=lang),
            value=editors,
            inline=False
        )
        contributors = self.ar_data.get('contributors', '') or 'None'
        contributors = ', '.join(f"<@{c}>" for c in contributors.split(',') if c) if contributors != 'None' else 'None'
        embed.add_field(
            name=localization.get("config", "ar.contributors", lang=lang),
            value=contributors,
            inline=False
        )
        editor_role = self.ar_data.get('editor_role')
        editor_role_str = f"<@&{editor_role}>" if editor_role else 'None'
        embed.add_field(
            name=localization.get("config", "ar.editor_role", lang=lang),
            value=editor_role_str,
            inline=True
        )
        permissions = self.ar_data.get('edit_permissions', '') or 'None'
        embed.add_field(
            name=localization.get("config", "ar.edit_permissions", lang=lang),
            value=permissions,
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "ar.arguments", lang=lang),
            value=self.ar_data['arguments'],
            inline=True
        )
        return embed

class AutoresponderCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.ar_messages = {}
        self.valid_permissions = {'edit', 'delete', 'add_language', 'edit_non_default', 'add_editors'}

    def check_restricted_placeholders(self, response: str, user: discord.Member) -> tuple[bool, str]:
        """Check if response contains restricted placeholders and if user has permission"""
        restricted_patterns = [
            r"\{dm(?::[^}]*)\}",  # {dm} or {dm:target}
            r"\{interaction:[^}]*\}",  # {interaction:type:value[:nametag]}
            r"\{delete\}",  # {delete}
            r"\{action:[^}]*\}",  # {action:action:nametag}
            r"\{role(?::[^:]*):[^}]*\}",  # {role[:action]:role_name}
            r"\{embed:[^}]*\}",  # {embed:name}
            r"\{user_infractions\}",  # staff_placeholders
            r"\{message_id\}",
            r"\{message\}",
            r"\{message_reactions\}",
            r"\{message_created\}",
            r"\{channel_last_message\}",
        ]
        lang = cfg.get_user_config(user.id, "language") or "en"
        staff_role = cfg.get_guild_config(user.guild.id, 'staff_role')
        for pattern in restricted_patterns:
            if re.search(pattern, response):
                if not user.guild_permissions.manage_guild and not (staff_role and any(role.id == staff_role for role in user.roles)):
                    return False, localization.get("config", "ar.restricted_placeholders", lang=lang)
        return True, ""

    async def check_permissions(self, user, guild_id, action, ar_data=None):
        """Check if user can perform action on autoresponder"""
        edit_role = cfg.get_guild_config(guild_id, 'autoresponder_edit_role')
        edit_perm = cfg.get_guild_config(guild_id, 'autoresponder_edit_permission')
        if edit_role and any(role.id == edit_role for role in user.roles):
            return True
        if getattr(user.guild_permissions, edit_perm, False):
            return True
        if ar_data:
            if str(user.id) == ar_data['creator_id']:
                return True
            editors = ar_data.get('editors', '').split(',') if ar_data.get('editors') else []
            permissions = ar_data.get('edit_permissions', '').split(',') if ar_data.get('edit_permissions') else []
            editor_role = ar_data.get('editor_role')
            guild = user.guild
            if editor_role and (editor_role == guild.default_role.id or any(role.id == editor_role for role in user.roles)):
                return action in permissions
            if str(user.id) in editors:
                return action in permissions
        return False

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author.bot or not message.guild:
            return

        guild_id = str(message.guild.id)
        lang = cfg.get_language(message.author.id, guild_id) or "en"
        triggers = get_guild_triggers(guild_id)

        for ar_data in triggers:
            trigger = ar_data["trigger"].lower()
            content = message.content.lower()

            if trigger in content:
                ar_name = ar_data["name"]
                ar_data_lang = get_autoresponder(guild_id, ar_name, lang)
                ar_data_en = get_autoresponder(guild_id, ar_name, "en")

                selected_data = ar_data_lang or ar_data_en
                if not selected_data:
                    continue


                arguments = selected_data.get('arguments', 'none')
                if arguments == 'user' and not re.search(r"<@!?(\d+)>", message.content):
                    continue

                data = selected_data["response"]
                if data:
                    response, reactions = await pl(message, data)
                    if isinstance(response, str):
                        print(f"Failed to process autoresponder '{ar_name}': {response}")
                        break

                    if response:
                        try:
                            print(f"Sending autoresponder '{ar_name}' in guild {guild_id} to {message.author.name}\nResponse:{response}\nEmbed: {response.get('embed')}\nView: {response.get('view')}")
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
                                "creator_id": selected_data["creator_id"],
                                "trigger": selected_data["trigger"],
                            }
                        except discord.Forbidden:
                            print(f"Failed to send autoresponder '{ar_name}' in guild {guild_id}: Bot lacks permissions")
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
            guild_id = str(reaction.message.guild.id)
            ar_data = get_autoresponder(guild_id, ar_info['name'], 'en')
            if str(reaction.emoji) == "🗑️" and await self.check_permissions(user, guild_id, 'delete', ar_data):
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
        pfx = cfg.get_guild_config(ctx.guild.id, "prefix") or " "
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
    async def ar_create(self, ctx, name: str):
        """create an autoresponder interactively"""
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        if not await self.check_permissions(ctx.author, guild_id, 'edit'):
            await ctx.send(localization.get("config", "ar.no_permission", lang=lang))
            return
        if autoresponder_exists(guild_id, name):
            await ctx.send(localization.get("config", "ar.already_exists", lang=lang, name=name))
            return

        await ctx.send(localization.get("config", "ar.create_prompt_trigger", lang=lang, name=name))
        try:
            trigger_msg = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=60)
            trigger = trigger_msg.content
            if re.search(r"\{[^}]*\}", trigger):
                await ctx.send(localization.get("config", "ar.invalid_trigger", lang=lang))
                return
        except asyncio.TimeoutError:
            await ctx.send(localization.get("config", "ar.timeout", lang=lang))
            return

        await ctx.send(localization.get("config", "ar.create_prompt_response", lang=lang, name=name))
        try:
            response_msg = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=60)
            response = response_msg.content
            allowed, error = self.check_restricted_placeholders(response, ctx.author)
            if not allowed:
                await ctx.send(error)
                return
        except asyncio.TimeoutError:
            await ctx.send(localization.get("config", "ar.timeout", lang=lang))
            return

        await ctx.send(localization.get("config", "ar.create_prompt_arguments", lang=lang, name=name))
        try:
            args_msg = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=60)
            arguments = args_msg.content.lower()
            if arguments not in ['none', 'user']:
                await ctx.send(localization.get("config", "ar.invalid_arguments", lang=lang))
                return
        except asyncio.TimeoutError:
            await ctx.send(localization.get("config", "ar.timeout", lang=lang))
            return

        await ctx.send(localization.get("config", "ar.create_prompt_language", lang=lang, name=name))
        try:
            lang_msg = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=60)
            language = lang_msg.content.lower()
        except asyncio.TimeoutError:
            language = cfg.get_guild_config(guild_id, 'language')

        create_autoresponder(
            guild_id, name, trigger, response, ctx.author.id, language,
            editor_role=ctx.guild.default_role.id, arguments=arguments
        )
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
            name=localization.get("config", "ar.preview_response", lang=lang),
            value=response[:100] + "..." if len(response) > 100 else response,
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "ar.arguments", lang=lang),
            value=arguments,
            inline=True
        )
        await ctx.send(embed=embed, view=edit_view(self.bot, get_autoresponder(guild_id, name, language), ctx.author.id, guild_id, language))

    @autoresponder.command(name="edit")
    async def ar_edit(self, ctx, name: str):
        """edit an autoresponder interactively"""
        guild_id = str(ctx.guild.id)
        lang = cfg.get_language(ctx.author.id, guild_id) or "en"
        ar_data = get_autoresponder(guild_id, name, lang) or get_autoresponder(guild_id, name, 'en')
        if not ar_data:
            await ctx.send(localization.get("config", "ar.not_found", lang=lang, name=name))
            return
        if not await self.check_permissions(ctx.author, guild_id, 'edit', ar_data):
            if not ar_data.get('edit_permissions') or 'edit_non_default' not in ar_data.get('edit_permissions', '').split(','):
                if ar_data['language'] != cfg.get_guild_config(guild_id, 'language'):
                    await ctx.send(localization.get("config", "ar.no_edit_permission", lang=lang, action="edit non-default language"))
                    return
            await ctx.send(localization.get("config", "ar.no_permission", lang=lang))
            return
        await ctx.send(embed=await edit_view(self.bot, ar_data, ctx.author.id, guild_id, ar_data['language']).create_edit_embed(ctx.author), view=edit_view(self.bot, ar_data, ctx.author.id, guild_id, ar_data['language']))

    @autoresponder.command(name="delete")
    async def ar_delete(self, ctx, name: str):
        """delete an autoresponder"""
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        ar_data = get_autoresponder(guild_id, name, 'en')  # Check permissions with 'en' version
        if not ar_data:
            await ctx.send(localization.get("config", "ar.not_found", lang=lang, name=name))
            return
        if not await self.check_permissions(ctx.author, guild_id, 'delete', ar_data):
            await ctx.send(localization.get("config", "ar.no_permission", lang=lang))
            return
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
                grouped[name] = {"trigger": ar["trigger"], "languages": [], "arguments": ar["arguments"]}
            grouped[name]["languages"].append(ar["language"])
        for name, data in grouped.items():
            languages = ", ".join(data["languages"])
            embed.add_field(
                name=name,
                value=f"{localization.get('config', 'ar.trigger', lang=lang)}: `{data['trigger']}`\n{localization.get('config', 'ar.language', lang=lang)}: {languages}\n{localization.get('config', 'ar.arguments', lang=lang)}: {data['arguments']}",
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
            await ctx.send(f"{localization.get("config", "ar.failure", lang=lang)}\nError:\n```python\n{error.original}\n```")

async def setup(bot):
    await bot.add_cog(AutoresponderCog(bot))