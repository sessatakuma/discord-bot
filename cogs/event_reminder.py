import asyncio
from datetime import datetime, timedelta, timezone

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.date import DateTrigger
from discord import app_commands
from discord.ext import commands

from config.settings import GUILD_ID, GeneralChannelId, MeetingChannelId, RoleId
from core.bot_core import KumaBot


def get_role_name(channel_name: str) -> str:
    if "🗿" in channel_name:
        return "staff"
    elif "🎨" in channel_name:
        return "design"
    elif "💻" in channel_name:
        return "tech"
    elif "🏫" in channel_name:
        return "content"
    return None


class EventReminder(commands.Cog):
    event_cmd = app_commands.Group(name="event", description="活動提醒相關指令")

    def __init__(self, bot: KumaBot):
        self.bot = bot
        self.scheduled_events: list[discord.ScheduledEvent] = []
        self.scheduler = AsyncIOScheduler()
        self.update_events_lock = asyncio.Lock()
        self.scheduler.start()

    def cog_unload(self):
        """Clean up scheduler when cog is unloaded"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def update(self):
        guild = self.bot.get_guild(GUILD_ID)
        if guild is None:
            return

        async with self.update_events_lock:
            try:
                events = await guild.fetch_scheduled_events()
            except Exception as e:
                print(f"Failed to fetch scheduled events: {e}")
                return

            # Clear existing scheduled jobs and events
            self.scheduler.remove_all_jobs()
            self.scheduled_events.clear()

            for event in events:
                if event.status != discord.EventStatus.scheduled:
                    continue
                if not (role_name := get_role_name(event.channel.name)):
                    continue
                if not (
                    channel := guild.get_channel(GeneralChannelId[role_name].value)
                ):
                    continue

                # Schedule reminder jobs for this event
                self._schedule_event_reminders(event, channel, RoleId[role_name].value)
                self.scheduled_events.append(event)

            self.scheduled_events = sorted(
                self.scheduled_events, key=lambda e: e.start_time
            )
            print(
                f"📅 Scheduled events: {[event.name for event in self.scheduled_events]}"
            )

    def _schedule_event_reminders(
        self, event: discord.ScheduledEvent, channel: discord.TextChannel, role_id: int
    ):
        """Schedule all reminder jobs for a single event"""
        start_time = event.start_time
        now = datetime.now(timezone.utc)

        # Schedule 6-hour reminder
        remind_6h = start_time - timedelta(hours=6)
        if remind_6h > now:
            self.scheduler.add_job(
                self._send_reminder,
                trigger=DateTrigger(run_date=remind_6h),
                args=[channel, role_id, event, "還有 6 小時，請先準備好開會大綱！"],
                id=f"{event.id}_6h",
                misfire_grace_time=60,
            )

        # Schedule 1-hour reminder
        remind_1h = start_time - timedelta(hours=1)
        if remind_1h > now:
            self.scheduler.add_job(
                self._send_reminder,
                trigger=DateTrigger(run_date=remind_1h),
                args=[channel, role_id, event, "還有 1 小時，準備要開會囉！"],
                id=f"{event.id}_1h",
                misfire_grace_time=60,
            )

        # Schedule start reminder
        if start_time > now:
            self.scheduler.add_job(
                self._send_reminder,
                trigger=DateTrigger(run_date=start_time),
                args=[channel, role_id, event, "現在開始！"],
                id=f"{event.id}_start",
                misfire_grace_time=60,
            )

    async def _send_reminder(
        self,
        channel: discord.TextChannel,
        role_id: int,
        event: discord.ScheduledEvent,
        message: str,
    ):
        """Send a reminder message for an event"""
        try:
            await channel.send(f"<@&{role_id}> [{event.name}]({event.url}) {message}")
        except Exception as e:
            print(f"Failed to send reminder for event {event.name}: {e}")

    # /event list
    @event_cmd.command(name="list", description="查詢已排程提醒的活動")
    async def event_list(self, interaction: discord.Interaction):
        if self.update_events_lock.locked():
            await interaction.response.send_message(
                "正在更新活動列表，請稍後再試。", ephemeral=True
            )
            return
        if not self.scheduled_events:
            await interaction.response.send_message(
                "目前尚未有任何活動被加入提醒。", ephemeral=True
            )
            return
        lines = []
        for event in self.scheduled_events:
            # Check if user has the role for this event
            role_name = MeetingChannelId(event.channel.id).name
            if role_name and interaction.user.get_role(RoleId[role_name].value):
                lines.append(
                    f"• {event.name} (開始於: <t:{int(event.start_time.timestamp())}:F>)"
                )
        msg = "已排程提醒的活動：\n" + "\n".join(lines)
        await interaction.response.send_message(msg, ephemeral=True)

    # /event today
    @event_cmd.command(name="today", description="查詢今天的活動")
    async def event_today(self, interaction: discord.Interaction):
        if self.update_events_lock.locked():
            await interaction.response.send_message(
                "正在更新活動列表，請稍後再試。", ephemeral=True
            )
            return
        today = datetime.now(timezone.utc).date()
        today_events = [
            event for event in self.scheduled_events if event.start_time.date() == today
        ]
        if not today_events:
            await interaction.response.send_message(
                "今天沒有任何活動。", ephemeral=True
            )
            return
        lines = []
        for event in today_events:
            # Check if user has the role for this event
            role_name = MeetingChannelId(event.channel.id).name
            if role_name and interaction.user.get_role(RoleId[role_name].value):
                lines.append(f"• [{event.name}]({event.url})")
        msg = "今天的活動：\n" + "\n".join(lines)
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: KumaBot):
    await bot.add_cog(EventReminder(bot))
