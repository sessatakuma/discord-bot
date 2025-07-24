import discord
from discord.ext import commands

from core.context_menu import setup_context_menu
from core.events import setup_events


def create_bot():
    intents = discord.Intents.default()
    bot = commands.Bot(command_prefix="!", intents=intents)

    setup_events(bot)
    setup_context_menu(bot)

    return bot
