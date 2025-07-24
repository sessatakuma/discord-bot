from discord.ext import commands

from config.settings import COGS


def setup_events(bot: commands.Bot):
    @bot.event
    async def setup_hook():
        """Load cogs when bot is ready"""
        failed_cogs = []
        for cog_name in COGS:
            try:
                await bot.load_extension(cog_name)
            except Exception as e:
                print(f"❌ Failed to load {cog_name}: {e}")
                failed_cogs.append(cog_name)

        if not failed_cogs:
            print("✅ All cogs loaded successfully")
        else:
            print(f"⚠️ {len(failed_cogs)} cog(s) failed to load")

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
