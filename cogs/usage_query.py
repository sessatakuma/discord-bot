from typing import Literal

from discord import Interaction, app_commands
from discord.ext import commands

from utils.api import fetch_usage


class UsageQueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="usage", description="查詢單字於NLB或NLT的用法")
    @app_commands.describe(word="要查詢的單字", site="查詢來源")
    @app_commands.choices(
        site=[
            app_commands.Choice(name="NLB", value="NLB"),
            app_commands.Choice(name="NLT", value="NLT"),
        ]
    )
    async def usage_query(self, interaction: Interaction, word: str, site: Literal["NLB", "NLT"]):
        await fetch_usage(interaction, word, site)


async def setup(bot):
    await bot.add_cog(UsageQueryCog(bot))
