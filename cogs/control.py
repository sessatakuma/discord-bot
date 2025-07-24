from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import COGS


class ControlCog(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @app_commands.command(name="ping", description="測試機器人是否正常運作")
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message("🏓 pong!")

    @app_commands.command(name="reload", description="Hot reload all Cog modules")
    @app_commands.checks.has_role(1377276760466391112)
    async def reload_all_cogs(self, interaction: Interaction):
        """Hot reload all cogs"""
        await interaction.response.defer()

        success_count = 0
        failed_cogs = []

        for cog_name in COGS:
            try:
                await self.bot.reload_extension(cog_name)
                success_count += 1
            except Exception as e:
                failed_cogs.append(f"{cog_name}: {str(e)}")

        # Send result message
        if failed_cogs:
            failed_msg = "\n".join([f"❌ {failed}" for failed in failed_cogs])
            await interaction.followup.send(
                f"✅ Successfully reloaded {success_count}/{len(COGS)} Cogs!\n\n**Failed:**\n{failed_msg}"
            )
        else:
            await interaction.followup.send(f"✅ Successfully reloaded all {success_count} Cogs!")

    @reload_all_cogs.error
    async def reload_error(self, interaction: Interaction, error: app_commands.AppCommandError):
        """Handle reload command errors"""
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message(
                "❌ You need one of the following roles to use this command: Developer, Admin, Bot Manager, Moderator",
                ephemeral=True,
            )
        else:
            await interaction.response.send_message("❌ An unknown error occurred")


async def setup(bot: commands.Bot):
    await bot.add_cog(ControlCog(bot))
