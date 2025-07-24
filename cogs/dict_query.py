from discord import Interaction, app_commands
from discord.ext import commands

from utils.api import fetch_dict_link


class DictQueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="dict", description="查詢Weblio字典連結")
    @app_commands.describe(word="要查詢的單字，支援多個單字，用空格或逗號(,)分隔")
    @app_commands.rename(word="單字")
    async def dict_query(self, interaction: Interaction, word: str):
        await fetch_dict_link(interaction, word)


async def dict_query_handler(interaction, words):
    await fetch_dict_link(interaction, words)


async def setup(bot):
    await bot.add_cog(DictQueryCog(bot))
