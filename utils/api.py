import aiohttp

from config.settings import API_URL


async def fetch_dict_link(interaction, words):
    # Remove extra spaces and split by spaces or commas
    word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]
    if not word_list:
        await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
        return
    await interaction.response.defer()
    results = []
    try:
        async with aiohttp.ClientSession() as session:
            for word in word_list:
                query_data = {"word": word}
                try:
                    async with session.post(f"{API_URL}/api/DictQuery/", json=query_data) as response:
                        if response.status == 200:
                            data = await response.json()
                            link: str = data["result"]
                            results.append(f"\U0001f4da **{word}**: {link}")
                        else:
                            results.append(f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}")
                except Exception as e:
                    results.append(f"❌ **{word}**: 發生錯誤")
                    print(f"dict_query error for '{word}': {e}")
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


async def fetch_usage(interaction, words, site):
    word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]
    if not word_list:
        await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
        return
    await interaction.response.defer()
    results = []
    try:
        async with aiohttp.ClientSession() as session:
            for word in word_list:
                query_data = {"word": word, "site": site}
                try:
                    async with session.post(f"{API_URL}/api/UsageQuery/URL/", json=query_data) as response:
                        if response.status == 200:
                            data = await response.json()
                            if data["status"] == 200:
                                items: list = data["result"]
                                if len(items) == 1:
                                    results.append(f'\U0001f4da **{items[0]["word"]}**: {items[0]["url"]}')
                                elif len(items) > 1:
                                    results.append(f"\U0001f4da **{word}**:")
                                    for item in items:
                                        results.append(f'- {item["word"]}: {item["url"]}')
                            elif data["status"] == 404:
                                results.append(f"❌ **{word}**: 找不到用法")
                            else:
                                results.append(f"❌ **{word}**: 查詢失敗\n錯誤訊息: {data['error']}")
                        else:
                            results.append(f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}")
                except Exception as e:
                    results.append(f"❌ **{word}**: 發生錯誤")
                    print(f"usage_query error for '{word}': {e}")
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
