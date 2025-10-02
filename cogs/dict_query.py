import asyncio
import requests
import aiohttp

from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs

from discord import Interaction, app_commands
from discord.ext import commands

from config.settings import API_URL

class DictQueryCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    def cog_unload(self):
        """Clean up if necessary when cog is unloaded"""
        pass

    @app_commands.command(name="dict", description="查詢Weblio字典連結")
    @app_commands.describe(word="要查詢的單字，支援多個單字，用空格或逗號(,)分隔")
    @app_commands.rename(word="單字")
    async def dict_query(self, interaction: Interaction, word: str):
        await fetch_dict_link(interaction, word)

async def setup(bot: commands.Bot):
    await bot.add_cog(DictQueryCog(bot))

async def dict_query_handler(interaction, words):
    await fetch_dict_link(interaction, words)

# 取得所有符合資料的 url
async def get_all_url(search_word: str) -> list:
    url = f"https://www.edrdg.org/jmwsgi/srchres.py?s1=1&y1=1&t1={search_word}&src=1&search=Search&svc=jmdict"

    try:
        response = requests.get(url)
        response.encoding = response.apparent_encoding
    except requests.exceptions.RequestException as e:
        raise RuntimeError(f"Network error: {str(e)}")

    # 判斷是否因為只有一個結果而直接跳轉
    if "entr.py" in response.url:
        entry_id = parse_qs(urlparse(response.url).query).get("e", [None])[0]
        return [f"https://www.edrdg.org/jmwsgi/entr.py?svc=jmdict&e={entry_id}"] if entry_id else []
    
    soup = BeautifulSoup(response.text, "html.parser")
    rows = soup.find_all("tr", class_="resrow")

    url_list = []
    for row in rows:
        inp = row.find("input", {"name": "e"})
        if inp and inp.has_attr("value"):
            url_list.append(f"https://www.edrdg.org/jmwsgi/entr.py?svc=jmdict&e={inp['value']}")

    return url_list

# 根據 url 清單回傳查詢結果
async def get_dict(url_list: list):
    results = []

    for url in url_list:
        try:
            response = requests.get(url)
            response.encoding = response.apparent_encoding
        except requests.exceptions.RequestException as e:
            raise RuntimeError(f"Network error: {str(e)}")

        soup = BeautifulSoup(response.text, "html.parser")

        try:
            kanji = [k.get_text(strip=True) for k in soup.select("span.kanj")]
            furigana = [k.get_text(strip=True) for k in soup.select("span.rdng")]

            definitions = []
            for sense in soup.select("tr.sense"):
                pos = [k.get_text(" ", strip=True) for k in sense.select("span.pos span.abbr")]
                meanings = [k.get_text(" ", strip=True).replace("▶", "").strip() for k in sense.select("span.glossx")]
                definitions.append(Definition(pos=pos, meanings=meanings))

            jmdict_id = soup.select_one('a[href^="srchres.py"]')
            id = int(jmdict_id.get_text(strip=True)) if jmdict_id else 0

            results.append(WordResult(
                kanji=kanji,
                furigana=furigana,
                definitions=definitions,
                id=id
            ))
        except Exception as e:
            raise RuntimeError(f"Parse error: {str(e)}")

    return results

async def fetch_dict_link(interaction: Interaction, words: str):
    # Remove extra spaces and split by spaces or commas
    word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]
    if not word_list:
        await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
        return
    await interaction.response.defer()

    # async def query_single_word(session: aiohttp.ClientSession, word: str) -> str:
    #     """Query a single word and return formatted result"""
    #     query_data = {"word": word}
    #     try:
    #         async with session.post(f"{API_URL}/api/DictQuery/", json=query_data) as response:
    #             if response.status == 200:
    #                 data = await response.json()
    #                 link: str = data["result"]
    #                 return f"📚 **{word}**: {link}"
    #             else:
    #                 return f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}"
    #     except Exception as e:
    #         print(f"dict_query error for '{word}': {e}")
    #         return f"❌ **{word}**: 發生錯誤"

    try:
        async with aiohttp.ClientSession() as session:
            # Process all words concurrently
            results = []
            for word in word_list:
                url_list = await get_all_url(session, word)
                if not url_list:
                    results.append(f"❌ **{word}**: 找不到結果")
                else:
                    word_defs = await get_dict(session, url_list)
                    results.extend([f"📚 **{word}** → {d}" for d in word_defs])

        if results:
            response_text = "\n".join(results)
            if len(response_text) > 2000:
                response_text = response_text[:1997] + "..."
            await interaction.followup.send(response_text)
        else:
            await interaction.followup.send("❌ 找不到結果")
    except Exception as e:
        await interaction.followup.send("❌ 發生錯誤，請稍後再試")
        print(f"dict_query general error: {e}")
