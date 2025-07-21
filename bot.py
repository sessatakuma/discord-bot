import os

import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

bot = commands.Bot(command_prefix=None, intents=discord.Intents.default())


@bot.tree.command(name="ping", description="Test if the Bot is working properly")
async def ping(interaction: discord.Interaction):
    await interaction.response.send_message("🏓 pong!")


@bot.tree.command(name="dict", description="Query weblio links (supports multiple words)")
async def dict_query(interaction: discord.Interaction, words: str):
    """Query word definitions for multiple words"""

    # Remove extra spaces and split by spaces or commas
    word_list = [word.strip() for word in words.replace(",", " ").split() if word.strip()]

    if not word_list:  # Check if no valid words provided
        await interaction.response.send_message("❌ Please provide valid words!", ephemeral=True)
        return

    # Respond first to avoid timeout
    await interaction.response.defer()

    results = []

    try:
        async with aiohttp.ClientSession() as session:
            for word in word_list:
                query_data = {"word": word}
                try:
                    async with session.post(f"{API_URL}/DictQuery/", json=query_data) as response:
                        if response.status == 200:
                            data = await response.json()
                            link = data["result"] if "result" in data else "No link found."
                            results.append(f"📚 **{word}**: {link}")
                        else:
                            results.append(f"❌ **{word}**: Query failed")
                except Exception as e:
                    results.append(f"❌ **{word}**: Error occurred")
                    print(f"dict_query error for '{word}': {e}")

            # Send all results
            if results:
                response_text = "\n".join(results)
                # Discord has a 2000 character limit for messages
                if len(response_text) > 2000:
                    response_text = response_text[:1997] + "..."
                await interaction.followup.send(response_text)
            else:
                await interaction.followup.send("❌ No results found.")

    except Exception as e:
        await interaction.followup.send("❌ An error occurred, please try again later.")
        print(f"dict_query general error: {e}")


@bot.event
async def on_ready():
    print(f"{bot.user} is now online!")
    try:
        commands = bot.tree.get_commands()
        print(f"Commands: {len(commands)}")
        synced = await bot.tree.sync()
        print(f"✅ Successfully synced {len(synced)} commands")
    except Exception as e:
        print(f"❌ Slash command sync failed: {e}")
    print("💡 Press Ctrl+C to stop the bot")


if __name__ == "__main__":
    bot.run(TOKEN)
