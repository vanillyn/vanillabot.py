import discord
from discord.ext import commands
import wikipediaapi
from src.utils import config, localization

TOPICS = [
    "lgbtq",
    "queer",
    "transgender",
    "trans",
    "non-binary",
    "gender",
    "intersex",
    "sexuality",
    "transition",
]


class Wiki(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="wiki")
    @commands.has_permissions(embed_links=True)
    async def wiki(self, ctx, *, query):
        user_id = ctx.author.id
        lang = config.get_user_config(user_id, "language") or "en"
        msg_type = config.get_user_config(user_id, "message_type") or "embed"

        wiki = wikipediaapi.Wikipedia(
            user_agent="berrylyn/0.1 (wiki/mod bot for queer-focused discord servers by @vanillyn, https://github.com/vanillyn/vanillabot.py)",
            language=lang,
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )

        page = wiki.page(query)

        if not page.exists():
            wiki = wikipediaapi.Wikipedia(
            user_agent="berrylyn/0.1 (wiki/mod bot for queer-focused discord servers by @vanillyn, https://github.com/vanillyn/vanillabot.py)",
            language="enlanguage",
            extract_format=wikipediaapi.ExtractFormat.WIKI,
        )
            page = wiki.page(query)

        if not page.exists():
            await ctx.send(localization.get("wiki", "not_found").format(query=query))
            return

        categories = page.categories.keys()
        if not any(any(kw in cat.lower() for kw in TOPICS) for cat in categories):
            await ctx.send(localization.get("wiki", "off_topic").format(query=query))
            return

        summary = page.summary.split("\n")[0]
        url = page.fullurl

        if msg_type == "embed":
            embed = discord.Embed(title=page.title, description=summary, color=0x738ADB)
            embed.set_footer(text=url)
            await ctx.send(embed=embed)
        else:
            msg = f"**{page.title}**\n{summary}\n<{url}>"
            await ctx.send(msg)


async def setup(bot):
    await bot.add_cog(Wiki(bot))
