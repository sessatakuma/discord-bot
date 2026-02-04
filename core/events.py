from discord import ScheduledEvent

from cogs.event_reminder import EventReminder
from config.logging import setup_logging
from core.bot_core import KumaBot

logger = setup_logging(__name__)


def setup_events(bot: KumaBot) -> None:
    @bot.event
    async def on_ready() -> None:
        logger.info(f"{bot.user} is now online!")

        # Sync slash commands
        try:
            synced = await bot.tree.sync()
            logger.info(f"Successfully synced {len(synced)} commands")
        except Exception as e:
            logger.error(f"Slash command sync failed: {e}")

        # Setup event scheduler
        event_reminder: EventReminder = bot.get_cog("EventReminder")  # type: ignore
        if event_reminder:
            logger.info("Setting up event scheduler...")
            await event_reminder.update()
        else:
            logger.warning(
                "EventReminder cog not found, skipping event scheduler setup"
            )

        logger.info("Press Ctrl+C to stop the bot")

    @bot.event
    async def on_scheduled_event_create(event: ScheduledEvent) -> None:
        event_reminder: EventReminder = bot.get_cog("EventReminder")  # type: ignore
        if event_reminder:
            await event_reminder.update()

    @bot.event
    async def on_scheduled_event_update(
        before: ScheduledEvent, after: ScheduledEvent
    ) -> None:
        event_reminder: EventReminder = bot.get_cog("EventReminder")  # type: ignore
        if event_reminder:
            await event_reminder.update()

    @bot.event
    async def on_scheduled_event_delete(event: ScheduledEvent) -> None:
        event_reminder: EventReminder = bot.get_cog("EventReminder")  # type: ignore
        if event_reminder:
            await event_reminder.update()
