import re
import discord
import src.utils.config as config

def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"

async def pl(message: discord.Message, text: str):
    reactions, interactions, actions, conditions, roles_to_modify = [], [], {}, [], []
    should_delete = False
    delete_response_delay = None
    dm_target = None
    embed_name = None

    patterns = {
        "interaction": r"\{interaction:([^:]*):([^:]*)(?::([^}]*))?\}",
        "action": r"\{action:([^:]*):([^}]*)\}",
        "dm": r"\{dm(?::([^}]*))?\}",
        "delete": r"\{delete\}",
        "delete_response": r"\{delete_response(?::(\d+))?\}",
        "if": r"\{if:([^:]*):([^:]*)(?::([^}]*))?\}",
        "role": r"\{role(?::([^:]*))?:([^}]*)\}",
        "embed": r"\{embed:([^}]*)\}",
        "react": r"\{react:(.*?)\}",
    }

    try:
        for emoji in re.findall(patterns["react"], text):
            reactions.append(emoji)
        text = re.sub(patterns["react"], "", text)

        for match in re.finditer(patterns["interaction"], text):
            x, y, z = match.groups()
            if not x or not y:
                return "Error: {interaction} requires type and value.", []
            if x not in ["reaction", "button"]:
                return "Error: {interaction} type must be 'reaction' or 'button'.", []
            nametag = z if z else y
            interactions.append({"type": x, "value": y, "nametag": nametag})
        text = re.sub(patterns["interaction"], "", text)

        for match in re.finditer(patterns["action"], text):
            x, y = match.groups()
            if not x or not y:
                return "Error: {action} requires action and nametag.", []
            actions[y] = x
        text = re.sub(patterns["action"], "", text)

        dm_match = re.search(patterns["dm"], text)
        if dm_match:
            target = dm_match.group(1) or "user"
            if target not in ["user", "mention"]:
                return "Error: {dm} target must be 'user' or 'mention'.", []
            dm_target = target
        text = re.sub(patterns["dm"], "", text)

        if re.search(patterns["delete"], text):
            should_delete = True
        text = re.sub(patterns["delete"], "", text)

        delete_response_match = re.search(patterns["delete_response"], text)
        if delete_response_match:
            delay = delete_response_match.group(1)
            try:
                delete_response_delay = int(delay) if delay else 10
            except ValueError:
                return "Error: Invalid delay for {delete_response}.", []
        text = re.sub(patterns["delete_response"], "", text)

        for match in re.finditer(patterns["if"], text):
            x, y, z = match.groups()
            if not x or not y:
                return "Error: {if} requires type and value.", []
            if x not in ["user", "channel", "role"]:
                return "Error: {if} type must be 'user', 'channel', or 'role'.", []
            action = z if z else "allow"
            if action not in ["allow", "ignore"]:
                return "Error: {if} action must be 'allow' or 'ignore'.", []
            conditions.append({"type": x, "value": y, "action": action})
        text = re.sub(patterns["if"], "", text)

        for match in re.finditer(patterns["role"], text):
            x, y = match.groups()
            if not y:
                return "Error: {role} requires a role.", []
            action = x if x else "add"
            if action not in ["add", "remove"]:
                return "Error: {role} action must be 'add' or 'remove'.", []
            roles_to_modify.append({"action": action, "role": y})
        text = re.sub(patterns["role"], "", text)

        embed_match = re.search(patterns["embed"], text)
        if embed_match:
            embed_name = embed_match.group(1)
        text = re.sub(patterns["embed"], "", text)
    except Exception as e:
        return f"Error: Failed to parse placeholders. ({e})", []

    if interactions and not actions:
        return "Error: {interaction} requires {action}.", []

    prefix = config.get_guild_config(message.guild.id, "prefix") or "y;"
    author, channel, guild, mention, dt = message.author, message.channel, message.guild, message.mentions, discord.utils.format_dt

    placeholders = {
        "{user}": author.mention,
        "{user_name}": author.name,
        "{user_id}": str(author.id),
        "{user_join_date}": dt(author.joined_at, "F"),
        "{user_creation_date}": dt(author.created_at, "F"),
        "{user_top_role}": author.top_role.name,
        "{user_avatar}": author.avatar.url if author.avatar else "",
        "{user_banner}": author.banner.url if author.banner else "",
        "{mention_name}": mention[0].name if mention else "[user]",
        "{mention_id}": str(mention[0].id) if mention else "[0000]",
        "{mention_join_date}": dt(mention[0].joined_at, "F") if mention else "[00-00-0000]",
        "{mention_avatar}": mention[0].avatar.url if mention and mention[0].avatar else "[user avatar]",
        "{channel}": channel.mention,
        "{channel_name}": channel.name,
        "{server_name}": guild.name,
        "{server_id}": str(guild.id),
        "{server_creation_date}": dt(guild.created_at, "F"),
        "{server_roles}": str(sum(1 for r in guild.roles if r.name != "@everyone")),
        "{server_channels}": str(len(guild.channels)),
        "{server_level}": str(guild.premium_tier),
        "{server_boosts}": str(guild.premium_subscription_count or 0),
        "{server_prefix}": prefix,
        "{server_icon}": guild.icon.url if guild.icon else "",
        "{member_count_ordinal}": ordinal(guild.member_count),
        "{member_count}": str(guild.member_count),
        "{member_count_ex_bots}": str(sum(1 for m in guild.members if not m.bot)),
        "{member_count_ex_bots_ordinal}": ordinal(sum(1 for m in guild.members if not m.bot)),
        "{time}": dt(message.created_at, "F"),
        "{date}": dt(message.created_at, "d"),
    }

    staff_placeholders = {
        "{user_infractions}": str(len(config.get_infractions(message.guild.id, message.author.id))),
        "{message_id}": str(message.id),
        "{message}": message.content,
        "{message_reactions}": ", ".join([f"{r.emoji} ({r.count})" for r in message.reactions]),
        "{message_created}": dt(message.created_at, "F"),
        "{channel_last_message}": dt(message.channel.last_message.created_at, "F") if getattr(message.channel, "last_message", None) else "[no message]"
    }

    for key, val in placeholders.items():
        text = text.replace(key, val)

    if message.author.guild_permissions.manage_guild:
        for key, val in staff_placeholders.items():
            text = text.replace(key, val)
    else:
        for key in staff_placeholders.keys():
            text = text.replace(key, "[staff only]")

    for condition in conditions:
        c_type, c_value, c_action = condition["type"], condition["value"], condition["action"]
        if c_type == "user":
            target = mention[0] if mention and c_value == mention[0].name else author
            if target.name == c_value and c_action == "ignore":
                return None, []
        elif c_type == "channel":
            if channel.name == c_value or (c_value.startswith("#") and channel.name == c_value[1:]):
                if c_action == "ignore":
                    return None, []
        elif c_type == "role":
            role = discord.utils.get(guild.roles, name=c_value)
            if role and role in author.roles and c_action == "ignore":
                return None, []

    response = {"text": text.strip(), "reactions": reactions, "buttons": [], "embed": None, "view": None, "delete_after": None}

    if embed_name:
        embed_config = config.get_guild_config(message.guild.id, f"embeds.{embed_name}")
        if embed_config:
            embed = discord.Embed()
            if embed_config.get("title"):
                embed.title = embed_config["title"]
            if embed_config.get("description"):
                embed.description = embed_config["description"]
            if embed_config.get("color"):
                try:
                    embed.color = discord.Color(embed_config["color"])
                except Exception:
                    return "Error: Invalid embed color.", []
            response["embed"] = embed
        else:
            return f"Error: Embed '{embed_name}' not found.", []

    for interaction in interactions:
        i_type, i_value, i_nametag = interaction["type"], interaction["value"], interaction["nametag"]
        if i_type == "reaction":
            try:
                import emoji
                is_unicode_emoji = emoji.is_emoji(i_value)
                is_custom_emoji = discord.utils.get(guild.emojis, name=i_value) is not None
                if not (is_unicode_emoji or is_custom_emoji):
                    return f"Error: Invalid emoji '{i_value}'.", []
                response["reactions"].append(i_value)
            except Exception:
                return f"Error: Invalid emoji '{i_value}'.", []
        elif i_type == "button":
            try:
                button = discord.ui.Button(label=i_value, custom_id=i_nametag, style=discord.ButtonStyle.primary)
                response["buttons"].append(button)
            except Exception:
                return "Error: Failed to create button.", []

    async def handle_interaction(interaction: discord.Interaction):
        nametag = interaction.data.get("custom_id")
        action = actions.get(nametag)
        if action and action.startswith("{role"):
            match = re.match(r"\{role(?::([^:]*))?:([^}]*)\}", action)
            if not match:
                await interaction.response.send_message("Error: Malformed {role} action.", ephemeral=True)
                return
            role_action, role_name = match.groups()
            role_action = role_action if role_action else "add"
            role = discord.utils.get(guild.roles, name=role_name)
            if role:
                try:
                    if role_action == "add":
                        await interaction.user.add_roles(role)
                        await interaction.response.send_message(f"Added role {role_name} to {interaction.user.mention}.", ephemeral=True)
                    elif role_action == "remove":
                        await interaction.user.remove_roles(role)
                        await interaction.response.send_message(f"Removed role {role_name} from {interaction.user.mention}.", ephemeral=True)
                except discord.Forbidden:
                    await interaction.response.send_message("Error: Bot lacks permission to manage roles.", ephemeral=True)
            else:
                await interaction.response.send_message("Error: Role not found.", ephemeral=True)
        else:
            await interaction.response.send_message("Error: Unknown action.", ephemeral=True)

    if response["buttons"]:
        view = discord.ui.View(timeout=None)
        for button in response["buttons"]:
            button.callback = handle_interaction
            view.add_item(button)
        response["view"] = view

    if dm_target:
        target = mention[0] if dm_target == "mention" and mention else author
        try:
            await target.send(text)
        except discord.Forbidden:
            return "Error: Cannot send DM to user.", []

    if should_delete:
        try:
            await message.delete()
        except discord.Forbidden:
            return "Error: Cannot delete message.", []

    if delete_response_delay:
        response["delete_after"] = delete_response_delay

    return response, reactions