import asyncio
from typing import Literal

import aiohttp
from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import API_URL


class UsageQueryCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="usage", description="查詢單字於NLB或NLT的用法")
    @app_commands.describe(word="要查詢的單字，支援多個單字，用空格或逗號(,)分隔", site="查詢來源，支援NLB或NLT")
    @app_commands.choices(
        site=[
            app_commands.Choice(name="NLB", value="NLB"),
            app_commands.Choice(name="NLT", value="NLT"),
        ]
    )
    @app_commands.rename(word="單字", site="來源")
    async def usage_query(self, interaction: Interaction, word: str, site: Literal["NLB", "NLT"]):
        await fetch_usage(interaction, word, site)


async def setup(bot: commands.Bot):
    await bot.add_cog(UsageQueryCog(bot))


async def fetch_usage(interaction: Interaction, words: str, site: Literal["NLB", "NLT"]):
    word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]
    if not word_list:
        await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
        return
    await interaction.response.defer()

    async def query_single_usage(session: aiohttp.ClientSession, word: str) -> str:
        """Query usage for a single word and return formatted result"""
        query_data = {"word": word, "site": site}
        try:
            async with session.post(f"{API_URL}/api/UsageQuery/URL/", json=query_data) as response:
                if response.status == 200:
                    data = await response.json()
                    if data["status"] == 200:
                        items: list = data["result"]
                        if len(items) == 1:
                            return f'📚 **{items[0]["word"]}**: {items[0]["url"]}'
                        elif len(items) > 1:
                            result_lines = [f"📚 **{word}**:"]
                            for item in items:
                                result_lines.append(f'- {item["word"]}: {item["url"]}')
                            return "\n".join(result_lines)
                    elif data["status"] == 404:
                        return f"❌ **{word}**: 找不到用法"
                    else:
                        return f"❌ **{word}**: 查詢失敗\n錯誤訊息: {data['error']}"
                else:
                    return f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}"
        except Exception as e:
            print(f"usage_query error for '{word}': {e}")
            return f"❌ **{word}**: 發生錯誤"

    try:
        async with aiohttp.ClientSession() as session:
            # Process all words concurrently
            tasks = [query_single_usage(session, word) for word in word_list]
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
        print(f"usage_query general error: {e}")
