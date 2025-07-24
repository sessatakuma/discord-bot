from discord import Interaction, app_commands
from discord.ext import commands


class PingCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ping", description="測試機器人是否正常運作")
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message("🏓 pong!")


async def setup(bot: commands.Bot):
    await bot.add_cog(PingCog(bot))
