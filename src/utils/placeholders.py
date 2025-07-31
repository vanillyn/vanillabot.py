import re
import discord

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

    text = re.sub(react_pattern, "", text)

    placeholders = {
        "{user}": message.author.mention,
        "{user_name}": message.author.name,
        "{user_id}": str(message.author.id),
        "{user_join_date}": discord.utils.format_dt(message.author.joined_at, "F"),
        "{user_creation_date}": discord.utils.format_dt(message.author.created_at, "F"),
        "{top_role}": message.author.top_role.name,
        "{mention_name}": message.mentions[0].name if message.mentions else "[user]",
        "{mention_id}": str(message.mentions[0].id) if message.mentions else "[0000]",
        "{mention_join_date}": discord.utils.format_dt(
            message.mentions[0].joined_at, "F"
        ) if message.mentions else "[00-00-0000]",
        "{member_count_ordinal}": ordinal(message.guild.member_count),
        "{member_count}": str(message.guild.member_count),
        "{channel}": message.channel.mention,
        "{channel_name}": message.channel.name,
        "{server_name}": message.guild.name,
        "{server_id}": str(message.guild.id),
        "{server_creation_date}": discord.utils.format_dt(message.guild.created_at, "F"),
        "{time}": discord.utils.format_dt(message.created_at, "F"),
        "{date}": discord.utils.format_dt(message.created_at, "d"),
    }

    for key, val in placeholders.items():
        text = text.replace(key, val)

    return text.strip(), reactions
