import discord
from discord.ext import commands
import json
import asyncio
import datetime
from src.utils.placeholders import pl
from src.utils.localization import localization
from src.utils.config import utils as db
import src.utils.config.utils as cfg

class ModalBasic(discord.ui.Modal):
    def __init__(self, embed_name, embed_config, message, lang):
        super().__init__(title=localization.get("config", "embed.modal_basic_title", lang=lang))
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.lang = lang
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.title", lang=lang),
            custom_id="title",
            placeholder="e.g., Welcome to {server_name}!",
            required=False,
            max_length=256,
            default=self.embed_config.get("title", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.description", lang=lang),
            custom_id="description",
            placeholder="e.g., Hello, {user}! Enjoy your stay.",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=4000,
            default=self.embed_config.get("description", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.color", lang=lang),
            custom_id="color",
            placeholder="e.g., 0x00FF00 for green",
            required=False,
            max_length=20,
            default=str(self.embed_config.get("color", ""))
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.timestamp", lang=lang),
            custom_id="timestamp",
            placeholder="Leave blank for no timestamp",
            required=False,
            max_length=30,
            default=self.embed_config.get("timestamp", "")
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            title = self.children[0].value
            description = self.children[1].value
            color_str = self.children[2].value
            timestamp_str = self.children[3].value

            color = None
            if color_str:
                try:
                    color = int(color_str, 16) if color_str.startswith("0x") else int(color_str)
                except ValueError:
                    await interaction.response.send_message(localization.get("config", "embed.error_invalid_color", lang=self.lang), ephemeral=True)
                    return

            self.embed_config.update({
                "name": self.embed_name,
                "title": title or None,
                "description": description or None,
                "color": color if color is not None else discord.Color.default().value,
                "timestamp": timestamp_str or None
            })

            embed = await self.build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message(localization.get("config", "embed.edit_success", lang=self.lang, name=self.embed_name), ephemeral=True, view=BuilderView(self.embed_name, self.embed_config, self.message, self.lang))
        except Exception as e:
            print(f"Failed to process basic modal: {e}")
            await interaction.response.send_message(localization.get("config", "embed.error_save", lang=self.lang), ephemeral=True)

    async def build_embed(self, interaction: discord.Interaction):
        embed = discord.Embed()
        if self.embed_config.get("title"):
            embed.title = self.embed_config["title"][:256]
        if self.embed_config.get("description"):
            embed.description = self.embed_config["description"][:4096]
        if self.embed_config.get("color"):
            try:
                embed.color = discord.Color(int(self.embed_config["color"]))
            except ValueError:
                pass
        if self.embed_config.get("footer", {}).get("text"):
            embed.set_footer(
                text=self.embed_config["footer"]["text"][:2048],
                icon_url=self.embed_config["footer"].get("icon_url")
            )
        if self.embed_config.get("thumbnail"):
            embed.set_thumbnail(url=self.embed_config["thumbnail"])
        if self.embed_config.get("image"):
            embed.set_image(url=self.embed_config["image"])
        if self.embed_config.get("author", {}).get("name"):
            embed.set_author(
                name=self.embed_config["author"]["name"][:256],
                url=self.embed_config["author"].get("url"),
                icon_url=self.embed_config["author"].get("icon_url")
            )
        if self.embed_config.get("timestamp"):
            try:
                embed.timestamp = datetime.datetime.fromisoformat(self.embed_config["timestamp"])
            except ValueError:
                pass
        for field in self.embed_config.get("fields", [])[:25]:
            embed.add_field(
                name=field["name"][:256],
                value=field["value"][:1024],
                inline=field.get("inline", False)
            )
        return embed

class ModalAdvanced(discord.ui.Modal):
    def __init__(self, embed_name, embed_config, message, lang):
        super().__init__(title=localization.get("config", "embed.modal_advanced_title", lang=lang))
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.lang = lang
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.footer_text", lang=lang),
            custom_id="footer_text",
            placeholder="e.g., Server ID: {server_id}",
            required=False,
            max_length=2048,
            default=self.embed_config.get("footer", {}).get("text", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.footer_icon", lang=lang),
            custom_id="footer_icon",
            placeholder="e.g., https://example.com/icon.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("footer", {}).get("icon_url", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.thumbnail", lang=lang),
            custom_id="thumbnail",
            placeholder="e.g., https://example.com/thumbnail.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("thumbnail", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.image", lang=lang),
            custom_id="image",
            placeholder="e.g., https://example.com/image.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("image", "")
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.author", lang=lang),
            custom_id="author",
            placeholder="e.g., {user} | https://example.com | https://example.com/icon.png",
            required=False,
            max_length=2000,
            default=f"{self.embed_config.get('author', {}).get('name', '')} | {self.embed_config.get('author', {}).get('url', '')} | {self.embed_config.get('author', {}).get('icon_url', '')}"
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            footer_text = self.children[0].value
            footer_icon = self.children[1].value
            thumbnail = self.children[2].value
            image = self.children[3].value
            author_str = self.children[4].value

            self.embed_config["footer"] = {
                "text": footer_text or None,
                "icon_url": footer_icon or None
            }
            self.embed_config["thumbnail"] = thumbnail or None
            self.embed_config["image"] = image or None
            author_parts = [part.strip() for part in author_str.split("|")] if author_str else []
            self.embed_config["author"] = {
                "name": author_parts[0] if len(author_parts) > 0 else None,
                "url": author_parts[1] if len(author_parts) > 1 else None,
                "icon_url": author_parts[2] if len(author_parts) > 2 else None
            }

            embed = await ModalBasic(self.embed_name, self.embed_config, self.message, self.lang).build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message(localization.get("config", "embed.edit_success", lang=self.lang, name=self.embed_name), ephemeral=True, view=BuilderView(self.embed_name, self.embed_config, self.message, self.lang))
        except Exception as e:
            print(f"Failed to process advanced modal: {e}")
            await interaction.response.send_message(localization.get("config", "embed.error_save", lang=self.lang), ephemeral=True)

class ModalField(discord.ui.Modal):
    def __init__(self, embed_name, embed_config, message, lang):
        super().__init__(title=localization.get("config", "embed.modal_field_title", lang=lang))
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.lang = lang
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.field_name", lang=lang),
            custom_id="name",
            placeholder="e.g., Info",
            required=True,
            max_length=256
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.field_value", lang=lang),
            custom_id="value",
            placeholder="e.g., This is some info.",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1024
        ))
        self.add_item(discord.ui.TextInput(
            label=localization.get("config", "embed.field_inline", lang=lang),
            custom_id="inline",
            placeholder="true or false",
            required=False,
            max_length=5,
            default="false"
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            name = self.children[0].value
            value = self.children[1].value
            inline_str = self.children[2].value.lower()
            inline = inline_str == "true"

            if "fields" not in self.embed_config:
                self.embed_config["fields"] = []
            self.embed_config["fields"].append({
                "name": name,
                "value": value,
                "inline": inline
            })

            embed = await ModalBasic(self.embed_name, self.embed_config, self.message, self.lang).build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message(localization.get("config", "embed.edit_success", lang=self.lang, name=self.embed_name), ephemeral=True, view=BuilderView(self.embed_name, self.embed_config, self.message, self.lang))
        except Exception as e:
            print(f"Failed to process field modal: {e}")
            await interaction.response.send_message(localization.get("config", "embed.error_save", lang=self.lang), ephemeral=True)

class BuilderView(discord.ui.View):
    def __init__(self, embed_name, embed_config, message, lang):
        super().__init__(timeout=300)
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.lang = lang

    async def check_permissions(self, user, guild_id, action, embed_data):
        server_config = cfg.get_guild_config(guild_id)
        edit_role = server_config.get('embed_edit_role')
        edit_perm = server_config.get('embed_edit_permission', 'manage_server')
        if edit_role and any(role.id == edit_role for role in user.roles):
            return True
        if getattr(user.guild_permissions, edit_perm, False):
            return True
        if str(user.id) == embed_data['creator_id']:
            return True
        editors = embed_data.get('editors', '').split(',') if embed_data.get('editors') else []
        permissions = embed_data.get('edit_permissions', '').split(',') if embed_data.get('edit_permissions') else []
        editor_role = embed_data.get('editor_role')
        guild = user.guild
        if editor_role and (editor_role == guild.default_role.id or any(role.id == editor_role for role in user.roles)):
            return action in permissions
        if str(user.id) in editors:
            return action in permissions
        return False

    @discord.ui.button(label="Edit Basic Info", style=discord.ButtonStyle.primary)
    async def basic(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'edit', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="edit basic info"), ephemeral=True)
            return
        await interaction.response.send_modal(ModalBasic(self.embed_name, self.embed_config, self.message, self.lang))

    @discord.ui.button(label="Edit Footer/Images", style=discord.ButtonStyle.primary)
    async def advanced(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'edit', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="edit footer/images"), ephemeral=True)
            return
        await interaction.response.send_modal(ModalAdvanced(self.embed_name, self.embed_config, self.message, self.lang))

    @discord.ui.button(label="Add/Edit Field", style=discord.ButtonStyle.primary)
    async def field(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'edit', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="edit fields"), ephemeral=True)
            return
        if len(self.embed_config.get("fields", [])) >= 25:
            await interaction.response.send_message(localization.get("config", "embed.error_field_limit", lang=self.lang), ephemeral=True)
            return
        await interaction.response.send_modal(ModalField(self.embed_name, self.embed_config, self.message, self.lang))

    @discord.ui.button(label="Edit Editors", style=discord.ButtonStyle.primary)
    async def edit_editors(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'add_editors', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="edit editors"), ephemeral=True)
            return
        editors = embed_data.get('editors', '') or 'None'
        await interaction.response.send_message(
            localization.get("config", "embed.edit_prompt_editors", lang=self.lang, editors=editors),
            ephemeral=True
        )
        try:
            msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "embed.cancel", lang=self.lang), ephemeral=True)
                return
            editors = embed_data.get('editors', '').split(',') if embed_data.get('editors') else []
            editors = set(filter(None, editors))
            for part in msg.content.split(','):
                if part.startswith('+') and part[1:].isdigit():
                    editors.add(part[1:])
                elif part.startswith('-') and part[1:] in editors:
                    editors.remove(part[1:])
                else:
                    await interaction.followup.send(localization.get("config", "embed.invalid_editors", lang=self.lang), ephemeral=True)
                    return
            db.update_embed(interaction.guild.id, self.embed_name, embed_data['language'], editors=','.join(editors))
            embed_data['editors'] = ','.join(editors)
            await interaction.followup.send(localization.get("config", "embed.edit_success", lang=self.lang, name=self.embed_name), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user, embed_data))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "embed.timeout", lang=self.lang), ephemeral=True)

    @discord.ui.button(label="Edit Permissions", style=discord.ButtonStyle.primary)
    async def edit_permissions(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'add_editors', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="edit permissions"), ephemeral=True)
            return
        permissions = embed_data.get('edit_permissions', '') or 'None'
        await interaction.response.send_message(
            localization.get("config", "embed.edit_prompt_permissions", lang=self.lang, permissions=permissions),
            ephemeral=True
        )
        try:
            msg = await interaction.client.wait_for('message', check=lambda m: m.author.id == interaction.user.id and m.channel.id == interaction.channel.id, timeout=60)
            if msg.content.lower() == 'cancel':
                await interaction.followup.send(localization.get("config", "embed.cancel", lang=self.lang), ephemeral=True)
                return
            valid_perms = {'edit', 'delete', 'add_language', 'edit_non_default', 'add_editors'}
            new_perms = set(msg.content.split(','))
            if not new_perms.issubset(valid_perms):
                await interaction.followup.send(localization.get("config", "embed.invalid_permissions", lang=self.lang), ephemeral=True)
                return
            db.update_embed(interaction.guild.id, self.embed_name, embed_data['language'], edit_permissions=','.join(new_perms))
            embed_data['edit_permissions'] = ','.join(new_perms)
            await interaction.followup.send(localization.get("config", "embed.edit_success", lang=self.lang, name=self.embed_name), ephemeral=True)
            await interaction.message.edit(embed=await self.create_edit_embed(interaction.user, embed_data))
        except asyncio.TimeoutError:
            await interaction.followup.send(localization.get("config", "embed.timeout", lang=self.lang), ephemeral=True)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.green)
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed_data = db.get_embed(interaction.guild.id, self.embed_name, self.embed_config.get('language', 'en'))
        if not await self.check_permissions(interaction.user, str(interaction.guild.id), 'edit', embed_data):
            await interaction.response.send_message(localization.get("config", "embed.no_edit_permission", lang=self.lang, action="save embed"), ephemeral=True)
            return
        try:
            if len(json.dumps(self.embed_config)) > 6000:
                await interaction.response.send_message(localization.get("config", "embed.error_character_limit", lang=self.lang), ephemeral=True)
                return
            contributors = embed_data.get('contributors', '').split(',') if embed_data.get('contributors') else []
            if str(interaction.user.id) not in contributors:
                contributors.append(str(interaction.user.id))
                db.update_embed(interaction.guild.id, self.embed_name, embed_data['language'], contributors=','.join(filter(None, contributors)))
            db.update_embed(interaction.guild.id, self.embed_name, embed_data['language'], embed_config=self.embed_config)
            embed = await ModalBasic(self.embed_name, self.embed_config, self.message, self.lang).build_embed(interaction)
            await self.message.edit(embed=embed, view=None)
            await interaction.response.send_message(localization.get("config", "embed.create_success", lang=self.lang, name=self.embed_name), ephemeral=True)
        except Exception as e:
            print(f"Failed to save embed: {e}")
            await interaction.response.send_message(localization.get("config", "embed.error_save", lang=self.lang), ephemeral=True)

    async def create_edit_embed(self, user, embed_data):
        lang = cfg.get_user_config(user.id, "language") or "en"
        embed_config = embed_data['embed']
        embed = discord.Embed(
            title=localization.get("config", "embed.info", lang=lang, name=embed_data['name']),
            color=discord.Color.blue()
        )
        embed.add_field(
            name=localization.get("config", "embed.name", lang=lang),
            value=embed_data['name'],
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "embed.language", lang=lang),
            value=embed_data['language'],
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "embed.creator", lang=lang),
            value=f"<@{embed_data['creator_id']}>",
            inline=True
        )
        editors = embed_data.get('editors', '') or 'None'
        editors = ', '.join(f"<@{e}>" for e in editors.split(',') if e) if editors != 'None' else 'None'
        embed.add_field(
            name=localization.get("config", "embed.editors", lang=lang),
            value=editors,
            inline=False
        )
        contributors = embed_data.get('contributors', '') or 'None'
        contributors = ', '.join(f"<@{c}>" for c in contributors.split(',') if c) if contributors != 'None' else 'None'
        embed.add_field(
            name=localization.get("config", "embed.contributors", lang=lang),
            value=contributors,
            inline=False
        )
        editor_role = embed_data.get('editor_role')
        editor_role_str = f"<@&{editor_role}>" if editor_role else 'None'
        embed.add_field(
            name=localization.get("config", "embed.editor_role", lang=lang),
            value=editor_role_str,
            inline=True
        )
        permissions = embed_data.get('edit_permissions', '') or 'None'
        embed.add_field(
            name=localization.get("config", "embed.edit_permissions", lang=lang),
            value=permissions,
            inline=True
        )
        embed.add_field(
            name=localization.get("config", "embed.title", lang=lang),
            value=embed_config.get('title', 'None')[:256],
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "embed.description", lang=lang),
            value=embed_config.get('description', 'None')[:100] + "..." if embed_config.get('description') and len(embed_config.get('description')) > 100 else embed_config.get('description', 'None'),
            inline=False
        )
        return embed

class EmbedCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.valid_permissions = {'edit', 'delete', 'add_language', 'edit_non_default', 'add_editors'}

    async def check_permissions(self, user, guild_id, action, embed_data=None):
        server_config = cfg.get_guild_config(guild_id)
        edit_role = server_config.get('embed_edit_role')
        edit_perm = server_config.get('embed_edit_permission', 'manage_server')
        if edit_role and any(role.id == edit_role for role in user.roles):
            return True
        if getattr(user.guild_permissions, edit_perm, False):
            return True
        if embed_data:
            if str(user.id) == embed_data['creator_id']:
                return True
            editors = embed_data.get('editors', '').split(',') if embed_data.get('editors') else []
            permissions = embed_data.get('edit_permissions', '').split(',') if embed_data.get('edit_permissions') else []
            editor_role = embed_data.get('editor_role')
            guild = user.guild
            if editor_role and (editor_role == guild.default_role.id or any(role.id == editor_role for role in user.roles)):
                return action in permissions
            if str(user.id) in editors:
                return action in permissions
        return False

    @commands.group(name="embed", invoke_without_command=True)
    async def embed_group(self, ctx: commands.Context):
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        pfx = cfg.get_guild_config(ctx.guild.id, "prefix") or "y;"
        embed = discord.Embed(
            title=localization.get("config", "embed.title", lang=lang),
            description=localization.get("config", "embed.description", lang=lang),
            color=discord.Color.blue()
        )
        embed.add_field(
            name=localization.get("config", "embed.create", lang=lang),
            value=f"{pfx}{localization.get('config', 'embed.cmds.create', lang=lang)}",
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "embed.edit", lang=lang),
            value=f"{pfx}{localization.get('config', 'embed.cmds.edit', lang=lang)}",
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "embed.delete", lang=lang),
            value=f"{pfx}{localization.get('config', 'embed.cmds.delete', lang=lang)}",
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "embed.list", lang=lang),
            value=f"{pfx}{localization.get('config', 'embed.cmds.list', lang=lang)}",
            inline=False
        )
        embed.add_field(
            name=localization.get("config", "embed.preview", lang=lang),
            value=f"{pfx}{localization.get('config', 'embed.cmds.preview', lang=lang)}",
            inline=False
        )
        await ctx.send(embed=embed, ephemeral=True)

    @embed_group.command(name="create")
    async def create(self, ctx: commands.Context, name: str):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        server_config = cfg.get_guild_config(guild_id)
        if not await self.check_permissions(ctx.author, guild_id, 'edit'):
            await ctx.send(localization.get("config", "embed.no_permission", lang=lang), ephemeral=True)
            return
        if not name.isalnum():
            await ctx.send(localization.get("config", "embed.invalid_name", lang=lang), ephemeral=True)
            return
        if db.get_embed(ctx.guild.id, name, 'en'):  # Check for any language
            await ctx.send(localization.get("config", "embed.already_exists", lang=lang, name=name), ephemeral=True)
            return
        await ctx.send(localization.get("config", "embed.create_prompt_language", lang=lang, name=name), ephemeral=True)
        try:
            lang_msg = await self.bot.wait_for('message', check=lambda m: m.author.id == ctx.author.id and m.channel.id == ctx.channel.id, timeout=60)
            language = lang_msg.content.lower()
        except asyncio.TimeoutError:
            language = server_config.get('language', 'en')
        embed_config = {}
        embed = discord.Embed(
            title=localization.get("config", "embed.create_success", lang=lang, name=name),
            description=localization.get("config", "embed.description", lang=lang),
            color=discord.Color.blue()
        )
        message = await ctx.send(embed=embed, ephemeral=True)
        db.create_embed(ctx.guild.id, name, embed_config, language, ctx.author.id, editor_role=ctx.guild.default_role.id)
        view = BuilderView(name, embed_config, message, lang)
        await message.edit(embed=await view.create_edit_embed(ctx.author, db.get_embed(ctx.guild.id, name, language)), view=view)

    @embed_group.command(name="edit")
    async def edit(self, ctx: commands.Context, name: str):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        server_config = cfg.get_guild_config(guild_id)
        language = server_config.get('language', 'en')
        embed_data = db.get_embed(guild_id, name, language) or db.get_embed(guild_id, name, 'en')
        if not embed_data:
            await ctx.send(localization.get("config", "embed.not_found", lang=lang, name=name), ephemeral=True)
            return
        if not await self.check_permissions(ctx.author, guild_id, 'edit', embed_data):
            if not embed_data.get('edit_permissions') or 'edit_non_default' not in embed_data.get('edit_permissions', '').split(','):
                if embed_data['language'] != server_config.get('language', 'en'):
                    await ctx.send(localization.get("config", "embed.no_edit_permission", lang=lang, action="edit non-default language"), ephemeral=True)
                    return
            await ctx.send(localization.get("config", "embed.no_permission", lang=lang), ephemeral=True)
            return
        embed_config = embed_data['embed']
        message = await ctx.send(embed=await BuilderView(name, embed_config, None, lang).create_edit_embed(ctx.author, embed_data), ephemeral=True)
        view = BuilderView(name, embed_config, message, lang)
        await message.edit(embed=await view.create_edit_embed(ctx.author, embed_data), view=view)

    @embed_group.command(name="delete")
    async def delete(self, ctx: commands.Context, name: str):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        embed_data = db.get_embed(guild_id, name, 'en')  # Check permissions with 'en' version
        if not embed_data:
            await ctx.send(localization.get("config", "embed.not_found", lang=lang, name=name), ephemeral=True)
            return
        if not await self.check_permissions(ctx.author, guild_id, 'delete', embed_data):
            await ctx.send(localization.get("config", "embed.no_permission", lang=lang), ephemeral=True)
            return
        if db.delete_embed(guild_id, name):
            await ctx.send(localization.get("config", "embed.delete_success", lang=lang, name=name), ephemeral=True)
        else:
            await ctx.send(localization.get("config", "embed.not_found", lang=lang, name=name), ephemeral=True)

    @embed_group.command(name="list")
    async def list(self, ctx: commands.Context):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        embeds = db.get_all_embeds(guild_id)
        if not embeds:
            await ctx.send(localization.get("config", "embed.no_embeds", lang=lang), ephemeral=True)
            return
        embed = discord.Embed(
            title=localization.get("config", "embed.list_success", lang=lang, guild=ctx.guild.name),
            color=discord.Color.blue()
        )
        grouped = {}
        for embed_data in embeds:
            name = embed_data["name"]
            if name not in grouped:
                grouped[name] = {"languages": []}
            grouped[name]["languages"].append(embed_data["language"])
        for name, data in grouped.items():
            languages = ", ".join(data["languages"])
            embed.add_field(
                name=name,
                value=f"{localization.get('config', 'embed.language', lang=lang)}: {languages}",
                inline=False
            )
        await ctx.send(embed=embed, ephemeral=True)

    @embed_group.command(name="preview")
    async def preview(self, ctx: commands.Context, name: str):
        guild_id = str(ctx.guild.id)
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        server_config = cfg.get_guild_config(guild_id)
        embed_data = db.get_embed(guild_id, name, lang) or db.get_embed(guild_id, name, server_config.get('language', 'en')) or db.get_embed(guild_id, name, 'en')
        if not embed_data:
            await ctx.send(localization.get("config", "embed.not_found", lang=lang, name=name), ephemeral=True)
            return
        response, reactions = await pl(ctx.message, f"{{embed:{name}}}")
        if isinstance(response, str):
            await ctx.send(response, ephemeral=True)
            return
        view = response.get("view")
        embed = response.get("embed")
        if not embed:
            await ctx.send(localization.get("config", "embed.not_found", lang=lang, name=name), ephemeral=True)
            return
        msg = await ctx.send(embed=embed, view=view, ephemeral=True)
        for reaction in reactions:
            try:
                await msg.add_reaction(reaction)
            except discord.Forbidden:
                await ctx.send(localization.get("config", "embed.error_reaction", lang=lang), ephemeral=True)
        if response.get("delete_after"):
            await asyncio.sleep(response["delete_after"])
            try:
                await msg.delete()
            except discord.Forbidden:
                await ctx.send(localization.get("config", "embed.error_delete", lang=lang), ephemeral=True)

    @embed_group.error
    @create.error
    @edit.error
    @delete.error
    @list.error
    @preview.error
    async def embed_error(self, ctx, error):
        lang = cfg.get_user_config(ctx.author.id, "language") or "en"
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(localization.get("config", "embed.argument_missing", lang=lang, arg=error.param.name), ephemeral=True)
        elif isinstance(error, commands.BadArgument):
            await ctx.send(localization.get("config", "embed.invalid_name", lang=lang), ephemeral=True)
        elif isinstance(error, commands.MissingPermissions):
            await ctx.send(localization.get("config", "embed.no_permission", lang=lang), ephemeral=True)
        elif isinstance(error, commands.CommandInvokeError):
            await ctx.send(localization.get("config", "embed.failure", lang=lang), ephemeral=True)

async def setup(bot):
    await bot.add_cog(EmbedCog(bot))