from discord import Interaction, Message
from discord.ext import commands

from cogs.dict_query import dict_query_handler


def setup_context_menu(bot: commands.Bot):
    @bot.tree.context_menu(name="查詢Weblio字典連結")
    async def dict_query_context_menu(interaction: Interaction, message: Message):
        await dict_query_handler(interaction, message.content)
