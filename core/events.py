from cogs.event_reminder import EventReminder
from core.bot_core import KumaBot


def setup_events(bot: KumaBot):
    @bot.event
    async def on_ready():
        print(f"🐻‍❄️ {bot.user} is now online!")

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            print(f"✅ Successfully synced {len(synced)} commands")
        except Exception as e:
            print(f"❌ Slash command sync failed: {e}")

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
