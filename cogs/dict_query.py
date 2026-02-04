import asyncio
from typing import TypedDict

import aiohttp
from discord import Interaction, app_commands
from discord.ext import commands

from config.logging import setup_logging
from config.settings import API_URL
from core.bot_core import KumaBot

logger = setup_logging(__name__)


async def dict_query_handler(
    interaction: Interaction, words: str, session: aiohttp.ClientSession
) -> None:
    await fetch_dict_link(interaction, words, session)


class DictQueryCog(commands.Cog):
    def __init__(self, bot: KumaBot) -> None:
        self.bot = bot

    async def cog_unload(self) -> None:
        """Clean up if necessary when cog is unloaded"""
        pass

    @app_commands.command(name="dict", description="查詢字典連結")
    @app_commands.describe(word="要查詢的單字，支援多個單字，用空格或逗號(,)分隔")
    @app_commands.rename(word="單字")
    async def dict_query(self, interaction: Interaction, word: str) -> None:
        await fetch_dict_link(interaction, word, self.bot.session)


async def setup(bot: KumaBot) -> None:
    await bot.add_cog(DictQueryCog(bot))


async def fetch_dict_link(
    interaction: Interaction, words: str, session: aiohttp.ClientSession
) -> None:
    # Remove extra spaces and split by spaces or commas
    word_list = [
        word.strip() for word in words.replace(",", " ").split() if word.strip()
    ]
    if not word_list:
        await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
        return
    await interaction.response.defer()

    async def query_single_word(word: str) -> str:
        """Query a single word and return formatted result"""
        query_data = {"word": word}
        try:
            async with session.post(
                f"{API_URL}/api/DictQuery/", json=query_data
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == 200:

                        class DataItem(TypedDict):
                            kanji: list[str]
                            furigana: list[str]
                            definitions: list[dict[str, list[str]]]

                        item: DataItem
                        ret = []
                        for idx, item in enumerate(data["result"], 1):
                            kanji = f"{idx}. {', '.join(item.get('kanji', ''))}"
                            furigana = f"【{', '.join(item.get('furigana', ''))}】"
                            definitions = ""
                            for definition in item.get("definitions", []):
                                pos = (
                                    f"({', '.join(p)})"
                                    if (p := definition.get("pos", []))
                                    else ""
                                )
                                meanings = (
                                    f"▶ {' ▶ '.join(definition.get('meanings', []))}"
                                )
                                definitions += f"> {pos} {meanings}\n"
                            ret.append(f"{kanji} {furigana}\n{definitions}")
                        return f"📚 **{word}**:\n{''.join(ret)}"
                    elif data["status"] == 404:
                        return f"❌ **{word}**: 查無結果"
                    else:
                        return f"❌ **{word}**: 查詢失敗，錯誤內容({data['status']}: \
                            {data['error'].get('message', '未知錯誤')})"
                else:
                    return f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}"
        except Exception as e:
            logger.error(f"dict_query error for '{word}': {e}")
            return f"❌ **{word}**: 發生錯誤"

    try:
        # Process all words concurrently
        tasks = [query_single_word(word) for word in word_list]
        results = await asyncio.gather(*tasks)

        if results:
            response_text = "\n".join(results)
            if len(response_text) > 2000:
                response_text = response_text[:1997] + "..."
            await interaction.followup.send(response_text)
        else:
            await interaction.followup.send("❌ 找不到結果")
    except Exception as e:
        await interaction.followup.send("❌ 發生錯誤，請稍後再試")
        logger.error(f"dict_query general error: {e}")
