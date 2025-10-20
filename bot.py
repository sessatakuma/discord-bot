from dotenv import load_dotenv

load_dotenv()
from config.settings import TOKEN
from core.bot_core import create_bot

if __name__ == "__main__":
    bot = create_bot()
    bot.run(TOKEN)
