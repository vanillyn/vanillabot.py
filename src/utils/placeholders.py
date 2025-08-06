import re
import discord
import src.utils.config as config

def ordinal(n: int):
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = ["th", "st", "nd", "rd", "th"][min(n % 10, 4)]
    return str(n) + suffix

async def pl(message: discord.Message, text: str):
    reactions = []

    react_pattern = r"\{react:(.*?)\}"
    reactions_found = re.findall(react_pattern, text)
    for emoji in reactions_found:
        reactions.append(emoji)

    # use these instead of message.*
    text = re.sub(react_pattern, "", text)
    prefix = config.get_guild_config(message.guild.id, "prefix")
    author = message.author
    channel = message.channel
    guild = message.guild
    mention = message.mentions
    dt = discord.utils.format_dt
    
    # regular old placeholders
    placeholders = {
        "{user}": author.mention,
        "{user_name}": author.name,
        "{user_id}": str(author.id),
        "{user_join_date}": dt(author.joined_at, "F"),
        "{user_creation_date}": dt(author.created_at, "F"),
        "{user_top_role}": author.top_role.name,
        "{user_avatar}":  author.avatar.url if author.avatar else "",
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
        "{server_channels}": str(sum(1 for c in guild.channels)),
        "{server_level}": str(guild.premium_tier),
        "{server_boosts}": str(guild.premium_subscription_count or 0),
        "{server_prefix}": prefix if prefix else "ly:",
        "{server_icon}": guild.icon.url if guild.icon else "",
        "{member_count_ordinal}": ordinal(guild.member_count),
        "{member_count}": str(guild.member_count),
        "{member_count_ex_bots}": str(sum(1 for m in guild.members if not m.bot)),
        "{member_count_ex_bots_ordinal}": ordinal(sum(1 for m in guild.members if not m.bot)),
        "{time}": dt(message.created_at, "F"),
        "{date}": dt(message.created_at, "d"),
        "{time_relative}": dt(message.created_at, "R"),
    }


    # placeholders that check for staff when used (like when reacted to or created)
    staff_placeholders = {
        "{user_infractions}": str(config.get_infractions(message.guild.id, message.author.id)),
        "{message_id}": str(message.id),
        "{message}": message.content,
        "{message_reactions}": ", ".join([f"{r.emoji} ({r.count})" for r in message.reactions]),
        "{message_created}": discord.utils.format_dt(message.created_at),
        "{channel_last_message}": discord.utils.format_dt(message.channel.last_message.created_at)
    }
    
    for key, val in placeholders.items():
        text = text.replace(key, val)
        
    # staff check
    if message.author.guild_permissions.manage_guild:
        for key, val in staff_placeholders.items():
            text = text.replace(key, val)
    else:
        for key in staff_placeholders.keys():
            text = text.replace(key, "[staff only]")

    return text.strip(), reactions
