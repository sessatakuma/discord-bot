import os

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

# Cogs to load
COGS = [
    "cogs.dict_query",
    "cogs.usage_query",
    "cogs.control",
    "cogs.mark_accent",
    "cogs.mark_furigana",
]
