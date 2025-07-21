import os
from typing import Literal

import aiohttp
import discord
from discord import app_commands
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")


class DiscordBot:
    def __init__(self):
        self.bot = commands.Bot(command_prefix=None, intents=discord.Intents.default())
        self.setup_events()
        self.setup_commands()
        self.setup_context_menu()

    def setup_events(self):
        """Setup bot events"""

        @self.bot.event
        async def on_ready():
            print(f"{self.bot.user} is now online!")
            try:
                commands = self.bot.tree.get_commands()
                print(f"Commands: {len(commands)}")
                synced = await self.bot.tree.sync()
                print(f"✅ Successfully synced {len(synced)} commands")
            except Exception as e:
                print(f"❌ Slash command sync failed: {e}")
            print("💡 Press Ctrl+C to stop the bot")

    def setup_commands(self):
        """Setup all bot commands"""

        @self.bot.tree.command(name="ping", description="測試機器人是否正常運作")
        async def ping(interaction: discord.Interaction):
            await interaction.response.send_message("🏓 pong!")

        @self.bot.tree.command(name="dict", description="查詢Weblio字典連結")
        @app_commands.describe(word="要查詢的單字")
        async def dict_query_command(interaction: discord.Interaction, word: str):
            """Slash command to query Weblio dictionary links"""
            await self.dict_query(interaction, word)

        @self.bot.tree.command(name="usage", description="查詢單字於NLB或NLT的用法")
        @app_commands.describe(word="要查詢的單字", site="查詢來源")
        @app_commands.choices(
            site=[
                app_commands.Choice(name="NLB", value="NLB"),
                app_commands.Choice(name="NLT", value="NLT"),
            ]
        )
        async def usage_query(interaction: discord.Interaction, word: str, site: Literal["NLB", "NLT"]):
            await self.usage_query(interaction, word, site)

    def setup_context_menu(self):
        """Setup context menu commands"""

        @self.bot.tree.context_menu(name="查詢Weblio字典連結")
        async def dict_query_context_menu(interaction: discord.Interaction, message: discord.Message):
            """Context menu command to query Weblio dictionary links"""
            await self.dict_query(interaction, message.content)

    async def dict_query(self, interaction: discord.Interaction, words: str):
        """Query word definitions for multiple words"""

        # Remove extra spaces and split by spaces or commas
        word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]

        if not word_list:  # Check if no valid words provided
            await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
            return

        # Respond first to avoid timeout
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
                                link: str = data["result"] if "result" in data else "找不到連結"
                                results.append(f"📚 **{word}**: {link}")
                            else:
                                results.append(f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}")
                    except Exception as e:
                        results.append(f"❌ **{word}**: 發生錯誤")
                        print(f"dict_query error for '{word}': {e}")

                # Send all results
                if results:
                    response_text = "\n".join(results)
                    # Discord has a 2000 character limit for messages
                    if len(response_text) > 2000:
                        response_text = response_text[:1997] + "..."
                    await interaction.followup.send(response_text)
                else:
                    await interaction.followup.send("❌ 找不到結果")

        except Exception as e:
            await interaction.followup.send("❌ 發生錯誤，請稍後再試")
            print(f"dict_query general error: {e}")

    async def usage_query(self, interaction: discord.Interaction, words: str, site: Literal["NLB", "NLT"]):
        """Query word usage from specified site"""

        # Remove extra spaces and split by spaces or commas
        word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]

        if not word_list:  # Check if no valid words provided
            await interaction.response.send_message("❌ 請提供有效的單字！", ephemeral=True)
            return

        # Respond first to avoid timeout
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
                                links: list = data["result"] if "result" in data else "找不到連結"
                                # TODO: Need to enhance the output format and return the word to the corrsponding link in api
                                results.append(f'📚 **{word}**: {", ".join(links)}')
                            else:
                                results.append(f"❌ **{word}**: 查詢失敗，錯誤代碼 {response.status}")
                    except Exception as e:
                        results.append(f"❌ **{word}**: 發生錯誤")
                        print(f"usage_query error for '{word}': {e}")

                # Send all results
                if results:
                    response_text = "\n".join(results)
                    # Discord has a 2000 character limit for messages
                    if len(response_text) > 2000:
                        response_text = response_text[:1997] + "..."
                    await interaction.followup.send(response_text)
                else:
                    await interaction.followup.send("❌ 找不到結果")

        except Exception as e:
            await interaction.followup.send("❌ 發生錯誤，請稍後再試")
            print(f"usage_query general error: {e}")

    def run(self):
        """Start the bot"""
        try:
            self.bot.run(TOKEN)
        except Exception as e:
            print(f"❌ Bot error: {e}")


if __name__ == "__main__":
    discord_bot = DiscordBot()
    discord_bot.run()
