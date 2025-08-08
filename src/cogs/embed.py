import discord
from discord.ext import commands
import json
import asyncio
import datetime
from src.utils.placeholders import pl
from src.utils.config import utils as db

class modal_basic(discord.ui.Modal, title="Basic Info"):
    def __init__(self, embed_name, embed_config, message):
        super().__init__()
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.add_item(discord.ui.TextInput(
            label="Title",
            custom_id="title",
            placeholder="e.g., Welcome to {server_name}!",
            required=False,
            max_length=256,
            default=self.embed_config.get("title", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Description",
            custom_id="description",
            placeholder="e.g., Hello, {user}! Enjoy your stay.",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=4000,
            default=self.embed_config.get("description", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Color (Hex, e.g., 0x00FF00)",
            custom_id="color",
            placeholder="e.g., 0x00FF00 for green",
            required=False,
            max_length=20,
            default=str(self.embed_config.get("color", ""))
        ))
        self.add_item(discord.ui.TextInput(
            label="Timestamp (ISO, e.g., 2025-08-07T12:00:00)",
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
                    await interaction.response.send_message("Invalid color format, use hex like 0xFF00FF or int", ephemeral=True)
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
            await interaction.response.send_message("Updated embed. Continue editing or press finish.", ephemeral=True, view=builder_view(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to process basic modal: {str(e)}", ephemeral=True)

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

class modal_advanced(discord.ui.Modal, title="Footer and Images"):
    def __init__(self, embed_name, embed_config, message):
        super().__init__()
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.add_item(discord.ui.TextInput(
            label="Footer Text",
            custom_id="footer_text",
            placeholder="e.g., Server ID: {server_id}",
            required=False,
            max_length=2048,
            default=self.embed_config.get("footer", {}).get("text", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Footer Icon URL",
            custom_id="footer_icon",
            placeholder="e.g., https://example.com/icon.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("footer", {}).get("icon_url", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Thumbnail URL",
            custom_id="thumbnail",
            placeholder="e.g., https://example.com/thumbnail.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("thumbnail", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Image URL",
            custom_id="image",
            placeholder="e.g., https://example.com/image.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("image", "")
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.embed_config["footer"] = {
                "text": self.children[0].value or "",
                "icon_url": self.children[1].value or ""
            }
            self.embed_config["thumbnail"] = self.children[2].value or ""
            self.embed_config["image"] = self.children[3].value or ""
            embed = await self.build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message("Updated embed. Continue editing or press finish.", ephemeral=True, view=builder_view(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to process advanced modal: {str(e)}", ephemeral=True)

    async def build_embed(self, interaction: discord.Interaction):
        return await modal_basic(self.embed_name, self.embed_config, self.message).build_embed(interaction)

class modal_author(discord.ui.Modal, title="Author"):
    def __init__(self, embed_name, embed_config, message):
        super().__init__()
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.add_item(discord.ui.TextInput(
            label="Author Name",
            custom_id="author_name",
            placeholder="e.g., {server_name} Staff",
            required=False,
            max_length=256,
            default=self.embed_config.get("author", {}).get("name", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Author URL",
            custom_id="author_url",
            placeholder="e.g., https://example.com",
            required=False,
            max_length=2000,
            default=self.embed_config.get("author", {}).get("url", "")
        ))
        self.add_item(discord.ui.TextInput(
            label="Author Icon URL",
            custom_id="author_icon",
            placeholder="e.g., https://example.com/icon.png",
            required=False,
            max_length=2000,
            default=self.embed_config.get("author", {}).get("icon_url", "")
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            self.embed_config["author"] = {
                "name": self.children[0].value or "",
                "url": self.children[1].value or "",
                "icon_url": self.children[2].value or ""
            }
            embed = await self.build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message("Updated embed. Continue editing or press finish.", ephemeral=True, view=builder_view(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to process author modal: {str(e)}", ephemeral=True)

    async def build_embed(self, interaction: discord.Interaction):
        return await modal_basic(self.embed_name, self.embed_config, self.message).build_embed(interaction)

class modal_field(discord.ui.Modal, title="Fields"):
    def __init__(self, embed_name, embed_config, message):
        super().__init__()
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message
        self.add_item(discord.ui.TextInput(
            label="Field Name",
            custom_id="field_name",
            placeholder="e.g., Rules",
            required=False,
            max_length=256
        ))
        self.add_item(discord.ui.TextInput(
            label="Field Value",
            custom_id="field_value",
            placeholder="e.g., Read the rules in {channel}.",
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=1024
        ))
        self.add_item(discord.ui.TextInput(
            label="Inline (true/false)",
            custom_id="field_inline",
            placeholder="e.g., true",
            required=False,
            max_length=5
        ))

    async def on_submit(self, interaction: discord.Interaction):
        try:
            if self.children[0].value and self.children[1].value:
                field = {
                    "name": self.children[0].value,
                    "value": self.children[1].value,
                    "inline": self.children[2].value.lower() == "true"
                }
                if "fields" not in self.embed_config:
                    self.embed_config["fields"] = []
                self.embed_config["fields"].append(field)
            embed = await self.build_embed(interaction)
            await self.message.edit(embed=embed)
            await interaction.response.send_message("Updated embed. Continue editing or press finish.", ephemeral=True, view=builder_view(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to process field modal: {str(e)}", ephemeral=True)

    async def build_embed(self, interaction: discord.Interaction):
        return await modal_basic(self.embed_name, self.embed_config, self.message).build_embed(interaction)

class starting_view(discord.ui.View):
    def __init__(self, embed_name, embed_config):
        super().__init__(timeout=None)
        self.embed_name = embed_name
        self.embed_config = embed_config

    @discord.ui.button(label="Start editing", style=discord.ButtonStyle.primary, custom_id="start_building")
    async def start_building(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            embed = discord.Embed(title="Making embed...", description=f"Editing `{self.embed_name}`", color=discord.Color.blue())
            await interaction.response.send_message(
                f"Editing `{self.embed_name}`",
                view=builder_view(self.embed_name, self.embed_config, interaction.message),
                embed=embed,
                ephemeral=True
            )
            self.message = interaction.message  # Store the message for later editing
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to start embed builder: {str(e)}", ephemeral=True)

class builder_view(discord.ui.View):
    def __init__(self, embed_name, embed_config, message):
        super().__init__(timeout=None)
        self.embed_name = embed_name
        self.embed_config = embed_config
        self.message = message

    @discord.ui.button(label="Basic Info", style=discord.ButtonStyle.primary, custom_id="basic_info")
    async def basic_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(modal_basic(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to open basic modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Advanced Info", style=discord.ButtonStyle.primary, custom_id="advanced_info")
    async def advanced_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(modal_advanced(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to open advanced modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Author", style=discord.ButtonStyle.primary, custom_id="author_info")
    async def author_info(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            await interaction.response.send_modal(modal_author(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to open author modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Fields", style=discord.ButtonStyle.primary, custom_id="add_field")
    async def add_field(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if len(self.embed_config.get("fields", [])) >= 25:
                await interaction.response.send_message("Error: Cannot add more than 25 fields.", ephemeral=True)
                return
            await interaction.response.send_modal(modal_field(self.embed_name, self.embed_config, self.message))
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to open field modal: {str(e)}", ephemeral=True)

    @discord.ui.button(label="Finish", style=discord.ButtonStyle.green, custom_id="finish")
    async def finish(self, interaction: discord.Interaction, button: discord.ui.Button):
        try:
            if len(json.dumps(self.embed_config)) > 6000:
                await interaction.response.send_message("Error: Embed exceeds 6000 character limit.", ephemeral=True)
                return
            db.create_embed(interaction.guild.id, self.embed_name, self.embed_config)
            embed = await modal_basic(self.embed_name, self.embed_config, self.message).build_embed(interaction)
            await self.message.edit(embed=embed, view=None)
            await interaction.response.send_message(f"Embed `{self.embed_name}` saved!", ephemeral=True)
        except Exception as e:
            await interaction.response.send_message(f"Error: Failed to save embed: {str(e)}", ephemeral=True)

class command_group(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.group(name="embed", invoke_without_command=True)
    @commands.has_permissions(manage_guild=True)
    async def embed_group(self, ctx: commands.Context):
        await ctx.send("Available subcommands: create, delete, list, preview", ephemeral=True)

    @embed_group.command(name="create")
    @commands.has_permissions(manage_guild=True)
    async def create(self, ctx: commands.Context, name: str):
        try:
            if not name.isalnum():
                await ctx.send("Error: Embed name must be alphanumeric.", ephemeral=True)
                return
            if db.get_embed(ctx.guild.id, name):
                await ctx.send(f"Error: Embed '{name}' already exists.", ephemeral=True)
                return
            embed = discord.Embed(title="Making an embed", description=f"Created embed `{name}`. Click the button to start editing.", color=discord.Color.blue())
            await ctx.send(embed=embed, view=starting_view(name, {}), ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error: Failed to start embed builder: {str(e)}", ephemeral=True)

    @embed_group.command(name="delete")
    @commands.has_permissions(manage_guild=True)
    async def delete(self, ctx: commands.Context, name: str):
        try:
            if db.delete_embed(ctx.guild.id, name):
                await ctx.send(f"Embed '{name}' deleted successfully.", ephemeral=True)
            else:
                await ctx.send(f"Error: Embed '{name}' not found.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error: Failed to delete embed: {str(e)}", ephemeral=True)

    @embed_group.command(name="list")
    @commands.has_permissions(manage_guild=True)
    async def list(self, ctx: commands.Context):
        try:
            embeds = db.get_all_embeds(ctx.guild.id)
            if not embeds:
                await ctx.send("No embeds found for this guild.", ephemeral=True)
                return
            embed = discord.Embed(title="Embed List", color=discord.Color.blue())
            for name, config_json in embeds:
                config = json.loads(config_json)
                field_value = f"Title: {config.get('title', 'None')[:50]}\n"
                field_value += f"Description Length: {len(config.get('description', ''))}\n"
                field_value += f"Fields: {len(config.get('fields', []))}\n"
                field_value += f"Has Footer: {'Yes' if config.get('footer', {}).get('text') else 'No'}\n"
                field_value += f"Has Thumbnail: {'Yes' if config.get('thumbnail') else 'No'}\n"
                field_value += f"Has Image: {'Yes' if config.get('image') else 'No'}\n"
                field_value += f"Has Author: {'Yes' if config.get('author', {}).get('name') else 'No'}"
                embed.add_field(name=name, value=field_value, inline=True)
            await ctx.send(embed=embed, ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error: Failed to list embeds: {str(e)}", ephemeral=True)

    @embed_group.command(name="preview")
    @commands.has_permissions(manage_guild=True)
    async def preview(self, ctx: commands.Context, name: str):
        try:
            response, reactions = await pl(ctx.message, f"{{embed:{name}}}")
            if isinstance(response, str):
                await ctx.send(response, ephemeral=True)
                return
            view = response.get("view")
            embed = response.get("embed")
            if not embed:
                await ctx.send(f"Error: Embed '{name}' not found or invalid.", ephemeral=True)
                return
            msg = await ctx.send(embed=embed, view=view, ephemeral=True)
            for reaction in reactions:
                try:
                    await msg.add_reaction(reaction)
                except discord.Forbidden:
                    await ctx.send("Error: Cannot add reactions.", ephemeral=True)
            if response.get("delete_after"):
                await asyncio.sleep(response["delete_after"])
                try:
                    await msg.delete()
                except discord.Forbidden:
                    await ctx.send("Error: Cannot delete preview.", ephemeral=True)
        except Exception as e:
            await ctx.send(f"Error: Failed to preview embed: {str(e)}", ephemeral=True)

async def setup(bot):
    await bot.add_cog(command_group(bot))