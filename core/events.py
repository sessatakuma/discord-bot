from discord.ext import commands


def setup_events(bot: commands.Bot):
    @bot.event
    async def setup_hook():
        """Load cogs when bot is ready"""
        await bot.load_extension("cogs.dict_query")
        await bot.load_extension("cogs.usage_query")
        await bot.load_extension("cogs.ping")
        print("✅ All cogs loaded successfully")

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
