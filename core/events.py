import aiohttp

from cogs.event_reminder import EventReminder
from config.settings import COGS
from core.bot_core import KumaBot


def setup_events(bot: KumaBot):
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
        print(f"🐻‍❄️ {bot.user} is now online!")

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            print(f"✅ Successfully synced {len(synced)} commands")
        except Exception as e:
            print(f"❌ Slash command sync failed: {e}")

        # Get aiohttp session
        if bot.session is None:
            bot.session = aiohttp.ClientSession()
            print("🌐 Aiohttp session created")

        # Setup event scheduler
        event_reminder: EventReminder = bot.get_cog("EventReminder")
        if event_reminder:
            print("🔔 Setting up event scheduler...")
            await event_reminder.update()
        else:
            print("⚠️ EventReminder cog not found, skipping event scheduler setup")

        print("💡 Press Ctrl+C to stop the bot")

    @bot.event
    async def on_scheduled_event_create(event):
        event_reminder: EventReminder = bot.get_cog("EventReminder")
        if event_reminder:
            await event_reminder.update()

    @bot.event
    async def on_scheduled_event_update(before, after):
        event_reminder: EventReminder = bot.get_cog("EventReminder")
        if event_reminder:
            await event_reminder.update()

    @bot.event
    async def on_scheduled_event_delete(event):
        event_reminder: EventReminder = bot.get_cog("EventReminder")
        if event_reminder:
            await event_reminder.update()
