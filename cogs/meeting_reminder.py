from datetime import datetime, timedelta

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from config.settings import GeneralChannelId, RoleId
from core.bot_core import KumaBot


def is_first_day_of_last_week() -> bool:
    today = datetime.now()
    year = today.year
    month = today.month
    # Next month first day
    if month == 12:
        next_month = datetime(year + 1, 1, 1)
    else:
        next_month = datetime(year, month + 1, 1)
    last_day = next_month - timedelta(days=1)
    last_week_start = last_day - timedelta(days=6)
    # Only trigger on the first day of last week
    return today.date() == last_week_start.date()


class MeetingReminder(commands.Cog):
    # meeting_cmd = app_commands.Group(name="meeting", description="活動提醒相關指令")

    def __init__(self, bot: KumaBot) -> None:
        self.bot = bot
        # Create the scheduler
        self.scheduler = AsyncIOScheduler()
        # Schedule the reminder job every day at 9:00
        self.scheduler.add_job(self._send_reminder, "cron", hour=9, minute=0)
        self.scheduler.start()

    async def cog_unload(self) -> None:
        """Clean up scheduler when cog is unloaded"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def _send_reminder(self) -> None:
        try:
            # Only remind on the first day of the last week of the month
            if is_first_day_of_last_week():
                channel = self.bot.get_channel(GeneralChannelId.staff.value)
                assert isinstance(channel, discord.TextChannel)
                await channel.send(
                    f"<@&{RoleId.staff.value}> ⏰ 本月最後一週了！ \
                        請尚未填寫的人填寫下個月的開會時間表，謝謝！"
                )
        except Exception as e:
            print(f"Error sending meeting reminder: {e}")

    # /meeting remind
    # @meeting_cmd.command(name="remind", description="提醒填寫下個月開會時間表")
    # async def meeting_remind(self, interaction: Interaction):
    #     channel = self.bot.get_channel(GeneralChannelId.staff.value)
    #     if channel:
    #         await channel.send(f"<@&{RoleId.staff.value}> ⏰ \
    #                               請尚未填寫的人填寫下個月的開會時間表，謝謝！")
    #         await interaction.response.send_message(
    #             "提醒訊息已發送！", ephemeral=True
    #         )
    #     else:
    #         await interaction.response.send_message(
    #             "找不到指定頻道！", ephemeral=True
    #         )


async def setup(bot: KumaBot) -> None:
    await bot.add_cog(MeetingReminder(bot))
