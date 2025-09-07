from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import API_URL


class MarkFuriganaCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_unload(self):
        """Clean up if necessary when cog is unloaded"""
        pass

    @app_commands.command(name="furigana", description="標記日文文字的假名")
    @app_commands.describe(text="要查詢的文字")
    @app_commands.rename(text="文字")
    async def usage_query(self, interaction: Interaction, text: str):
        await mark_furigana(interaction, text)


async def setup(bot: commands.Bot):
    await bot.add_cog(MarkFuriganaCog(bot))


async def mark_furigana(interaction: Interaction, text: str):
    await interaction.response.send_message("天気(てんき)がいいから、散歩(さんぽ)しましょう。")
