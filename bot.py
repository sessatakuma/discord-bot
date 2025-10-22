import discord

from config.settings import TOKEN
from core.bot_core import KumaBot
from core.context_menu import setup_context_menu
from core.events import setup_events

if __name__ == "__main__":
    intents = discord.Intents.default()
    bot = KumaBot(command_prefix="!", intents=intents)

    setup_events(bot)
    setup_context_menu(bot)
    try:
        bot.run(TOKEN)
    finally:
        print("✅ Bot has been shut down")
