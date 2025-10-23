from discord import Interaction, Message

from cogs.dict_query import dict_query_handler
from cogs.mark_text import mark_text_handler
from cogs.usage_query import usage_query_handler
from core.bot_core import KumaBot


def setup_context_menu(bot: KumaBot):
    @bot.tree.context_menu(name="查詢字典")
    async def dict_query_context_menu(interaction: Interaction, message: Message):
        await dict_query_handler(interaction, message.content)

    @bot.tree.context_menu(name="查詢NLB用法")
    async def usage_query_nlb_context_menu(interaction: Interaction, message: Message):
        await usage_query_handler(interaction, message.content, "NLB")

    @bot.tree.context_menu(name="查詢NLT用法")
    async def usage_query_nlt_context_menu(interaction: Interaction, message: Message):
        await usage_query_handler(interaction, message.content, "NLT")

    @bot.tree.context_menu(name="標記日文假名和音調")
    async def mark_text_context_menu(interaction: Interaction, message: Message):
        await mark_text_handler(interaction, message.content)
