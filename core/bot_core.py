import aiohttp
from discord.ext import commands


class KumaBot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session: aiohttp.ClientSession | None = None

    async def close(self):
        """Override close to ensure aiohttp session is closed"""
        if self.session:
            await self.session.close()
            print("🌐 Aiohttp session closed")
        await super().close()
