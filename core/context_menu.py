from discord import Interaction, Message, app_commands

from cogs.dict_query import dict_query_handler


def setup_context_menu(bot):
    @bot.tree.context_menu(name="查詢Weblio字典連結")
    async def dict_query_context_menu(interaction: Interaction, message: Message):
        await dict_query_handler(interaction, message.content)
