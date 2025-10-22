import asyncio

from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import COGS, RoleId
from core.bot_core import KumaBot


class ControlCog(commands.Cog):
    def __init__(self, bot: KumaBot):
        self.bot = bot

    @app_commands.command(name="ping", description="測試機器人是否正常運作")
    async def ping(self, interaction: Interaction):
        await interaction.response.send_message("🏓 pong!", ephemeral=True)

    @app_commands.command(name="reload", description="Hot reload all Cog modules")
    @app_commands.checks.has_role(RoleId.tech.value)
    async def reload_all_cogs(self, interaction: Interaction):
        """Hot reload all cogs"""
        await interaction.response.defer()

        success_count = 0
        failed_cogs = []

        # Use asyncio.gather with return_exceptions=True to continue even if some cogs fail
        results = await asyncio.gather(
            *[self.bot.reload_extension(cog_name) for cog_name in COGS],
            return_exceptions=True,
        )

        # Process results
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                failed_cogs.append(f"{COGS[i]}: {str(result)}")
            else:
                success_count += 1

        # Send result message
        if failed_cogs:
            failed_msg = "\n".join([f"❌ {failed}" for failed in failed_cogs])
            await interaction.followup.send(
                f"✅ Successfully reloaded {success_count}/{len(COGS)} Cogs!\n\n**Failed:**\n{failed_msg}",
                ephemeral=True,
            )
        else:
            await interaction.followup.send(
                f"✅ Successfully reloaded all {success_count} Cogs!", ephemeral=True
            )

    @reload_all_cogs.error
    async def reload_error(
        self, interaction: Interaction, error: app_commands.AppCommandError
    ):
        """Handle reload command errors"""
        if isinstance(error, app_commands.MissingAnyRole):
            await interaction.response.send_message(
                "❌ You do not have permission to use this command.", ephemeral=True
            )
        else:
            # Handle all other errors including system-level failures
            error_msg = f"❌ Reload failed: {str(error)}"
            # Extract the original exception if it's wrapped in AppCommandError
            if hasattr(error, "original"):
                error_msg = f"❌ Reload failed: {str(error.original)}"

            if interaction.response.is_done():
                await interaction.followup.send(error_msg, ephemeral=True)
            else:
                await interaction.response.send_message(error_msg, ephemeral=True)


async def setup(bot: KumaBot):
    await bot.add_cog(ControlCog(bot))
