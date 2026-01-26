from typing import Any

import aiohttp
from discord.ext import commands

from config.googlesheet import get_user_mapping
from config.logging import setup_logging
from config.settings import COGS

logger = setup_logging(__name__)


class KumaBot(commands.Bot):
    session: aiohttp.ClientSession
    user_mapping: dict[str, dict[str, str]]

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)

    async def setup_hook(self) -> None:
        # Load cogs
        failed_cogs = []
        for cog_name in COGS:
            try:
                await self.load_extension(cog_name)
            except Exception as e:
                logger.error(f"Failed to load {cog_name}: {e}")
                failed_cogs.append(cog_name)

        if not failed_cogs:
            logger.info("All cogs loaded successfully")
        else:
            logger.error(f"{len(failed_cogs)} cog(s) failed to load")

        # Get aiohttp session
        self.session = aiohttp.ClientSession()
        logger.info("Aiohttp session created")
        # Get user mapping
        self.user_mapping = await get_user_mapping()
        logger.info(f"{len(self.user_mapping)} users mapping loaded")

    async def close(self) -> None:
        """Override close to ensure aiohttp session is closed"""
        if self.session:
            await self.session.close()
            print("Aiohttp session closed")
        await super().close()
