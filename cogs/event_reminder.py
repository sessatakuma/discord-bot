import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands

from config.settings import GUILD_ID, GeneralChannelId, RoleId


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
    reminder = app_commands.Group(name="reminder", description="活動提醒相關指令")

    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.scheduled_events: list[discord.ScheduledEvent] = []
        self.reminder_tasks: list[asyncio.Task] = []
        self.lock = asyncio.Lock()
        self.updating_events = False

    async def update_events(self):
        async with self.lock:
            self.updating_events = True
            guild = self.bot.get_guild(GUILD_ID)
            if guild is None:
                return

            # Cancel all existing tasks
            for task in self.reminder_tasks:
                if not task.done():
                    task.cancel()
            self.reminder_tasks.clear()
            self.scheduled_events.clear()

            events = await guild.fetch_scheduled_events()
            for event in events:
                if event.status != discord.EventStatus.scheduled:
                    continue
                role_name = get_role_name(event.channel.name)
                if not role_name:
                    continue
                channel = guild.get_channel(GeneralChannelId[role_name].value)
                if not channel:
                    continue
                self.reminder_tasks.append(
                    self.bot.loop.create_task(self.event_reminder(event, channel, RoleId[role_name].value))
                )
                self.scheduled_events.append(event)
            self.scheduled_events = sorted(self.scheduled_events, key=lambda e: e.start_time)

            print(f"📅 Scheduled events: {[event.name for event in self.scheduled_events]}")
            self.updating_events = False

    async def event_reminder(self, event: discord.ScheduledEvent, channel: discord.TextChannel, role_id: int):
        start_time = event.start_time
        timestamp = int(start_time.timestamp())
        remind_6h = start_time - timedelta(hours=6)
        remind_1h = start_time - timedelta(hours=1)

        # Remind 6 hours before the event
        now = datetime.now(timezone.utc)
        wait_6h = (remind_6h - now).total_seconds()
        if wait_6h > 0:
            await discord.utils.sleep_until(remind_6h)
            await channel.send(
                f"<@&{role_id}>「{event.name}」還有 6 小時，請先準備好開會大綱！ 開始時間: <t:{timestamp}:t>"
            )

        # Remind 1 hour before the event
        now = datetime.now(timezone.utc)
        wait_1h = (remind_1h - now).total_seconds()
        if wait_1h > 0:
            await discord.utils.sleep_until(remind_1h)
            await channel.send(f"<@&{role_id}>「{event.name}」還有 1 小時，準備要開會囉！ 開始時間: <t:{timestamp}:t>")

        # Remind at the start of the event
        now = datetime.now(timezone.utc)
        wait_start = (start_time - now).total_seconds()
        if wait_start > 0:
            await discord.utils.sleep_until(start_time)
            await channel.send(f"<@&{role_id}>「{event.name}」現在開始！")

    # /reminder list
    @reminder.command(name="list", description="查詢已排程提醒的活動")
    async def reminder_list(self, interaction: discord.Interaction):
        if self.updating_events:
            await interaction.response.send_message("正在更新活動列表，請稍後再試。", ephemeral=True)
            return
        if not self.scheduled_events:
            await interaction.response.send_message("目前尚未有任何活動被加入提醒。", ephemeral=True)
            return
        lines = []
        for event in self.scheduled_events:
            # Check if user has the role for this event
            if not event.channel.permissions_for(interaction.user).read_messages:
                continue
            lines.append(f"• {event.name} (開始於: <t:{int(event.start_time.timestamp())}:F>)")
        msg = "已排程提醒的活動：\n" + "\n".join(lines)
        await interaction.response.send_message(msg, ephemeral=True)


async def setup(bot: commands.Bot):
    await bot.add_cog(EventReminder(bot))
