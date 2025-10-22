import aiohttp
from discord.ext import commands

from config.settings import COGS


class KumaBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession | None = None

    async def setup_hook(self):
        # Load cogs
        failed_cogs = []
        for cog_name in COGS:
            try:
                await self.load_extension(cog_name)
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")
                failed_cogs.append(cog_name)

        if not failed_cogs:
            print("✅ All cogs loaded successfully")
        else:
            print(f"⚠️ {len(failed_cogs)} cog(s) failed to load")

        # Get aiohttp session
        if self.session is None:
            self.session = aiohttp.ClientSession()
            print("🌐 Aiohttp session created")

    async def close(self):
        """Override close to ensure aiohttp session is closed"""
        if self.session:
            await self.session.close()
            print("🌐 Aiohttp session closed")
        await super().close()
