from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import discord
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from discord.ext import commands

from config.logging import setup_logging
from config.settings import GUILD_ID, RoleId, WeeklyUpdateChannelId
from core.bot_core import KumaBot

logger = setup_logging(__name__)

TAIWAN_TZ = ZoneInfo("Asia/Taipei")


class WeeklyUpdateReminder(commands.Cog):
    def __init__(self, bot: KumaBot) -> None:
        self.bot = bot
        # Create the scheduler with Taiwan timezone
        self.scheduler = AsyncIOScheduler(timezone=TAIWAN_TZ)
        # Schedule Monday morning reminder at 10:00
        self.scheduler.add_job(
            self._send_morning_reminder, "cron", day_of_week="mon", hour=10, minute=0
        )
        # Schedule evening reminders from 18:00 to 23:00 every hour on Monday
        for hour in range(18, 24):
            self.scheduler.add_job(
                self._send_evening_reminder,
                "cron",
                day_of_week="mon",
                hour=hour,
                minute=0,
            )
        self.scheduler.start()

    async def cog_unload(self) -> None:
        """Clean up scheduler when cog is unloaded"""
        if self.scheduler.running:
            self.scheduler.shutdown()

    async def _send_morning_reminder(self) -> None:
        """Send morning reminder at 10:00 AM on Monday"""
        try:
            guild = self.bot.get_guild(GUILD_ID)
            if not isinstance(guild, discord.Guild):
                logger.error("Guild not found")
                return

            # Send reminder to each group's weekly update channel
            for channel_enum in WeeklyUpdateChannelId:
                role_name = channel_enum.name
                channel_id = channel_enum.value
                channel = guild.get_channel(channel_id)
                if not isinstance(channel, discord.TextChannel):
                    logger.error(f"Channel not found for {role_name}")
                    continue
                assert isinstance(channel, discord.TextChannel), (
                    "Channel must be a TextChannel"
                )

                await channel.send("[提醒] 今天是週一，請各位記得回報本週的進度狀況！")
                logger.info(f"Morning reminder sent to {role_name} channel")
        except Exception as e:
            logger.error(f"Error sending morning reminder: {e}")

    async def _check_reported_members(self, channel: discord.TextChannel) -> set[int]:
        """Check which members have reported today by checking channel messages"""
        reported_members: set[int] = set()

        try:
            # Calculate start of today in Taiwan time, then convert to UTC
            now_taiwan = datetime.now(TAIWAN_TZ)
            start_of_day_taiwan = now_taiwan.replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start_of_day_utc = start_of_day_taiwan.astimezone(timezone.utc)

            # Get all messages from today
            async for message in channel.history(after=start_of_day_utc, limit=1000):
                # Only count non-bot messages
                logger.debug(
                    f"Checking message from {message.author} at {message.created_at}, "
                    f"with content: {message.content}"
                )
                if not message.author.bot:
                    reported_members.add(message.author.id)

        except Exception as e:
            logger.error(f"Error checking reported members: {e}")

        return reported_members

    async def _get_unreported_members(
        self, guild: discord.Guild, role_name: str, reported_members: set[int]
    ) -> list[discord.Member]:
        """Get list of members with the role who haven't reported yet"""
        unreported: list[discord.Member] = []

        try:
            role_id = RoleId[role_name].value
            role = guild.get_role(role_id)

            if not isinstance(role, discord.Role):
                logger.error(f"Role not found for {role_name}")
                return unreported

            if len(role.members) == 0:
                logger.error(f"No members found with role {role_name}")
                return unreported

            for member in role.members:
                logger.debug(f"Checking member {member} with ID {member.id}")

                # Add to unreported list if member hasn't reported and is not a bot
                if member.id not in reported_members and not member.bot:
                    unreported.append(member)

        except Exception as e:
            logger.error(f"Error getting unreported members: {e}")

        return unreported

    async def _send_evening_reminder(self) -> None:
        """Send evening reminder from 6 PM to 11 PM, tagging unreported members"""
        try:
            guild = self.bot.get_guild(GUILD_ID)
            if not isinstance(guild, discord.Guild):
                logger.error("Guild not found")
                return

            # Check and remind for each group
            for channel_enum in WeeklyUpdateChannelId:
                role_name = channel_enum.name
                channel_id = channel_enum.value
                channel = guild.get_channel(channel_id)
                if not isinstance(channel, discord.TextChannel):
                    logger.error(f"Channel not found for {role_name}")
                    continue

                # Check who has reported today
                reported_members = await self._check_reported_members(channel)

                # Get unreported members
                unreported = await self._get_unreported_members(
                    guild, role_name, reported_members
                )

                # Send reminder if there are unreported members
                if unreported:
                    # Create mentions for unreported members
                    mentions = " ".join([member.mention for member in unreported])
                    await channel.send(
                        f"[提醒] 以下成員尚未回報本週進度，請記得回報：\n{mentions}"
                    )
                    logger.info(
                        f"Evening reminder sent to {role_name} channel "
                        f"for {len(unreported)} unreported members"
                    )
                else:
                    logger.info(f"All members in {role_name} have reported")

        except Exception as e:
            logger.error(f"Error sending evening reminder: {e}")


async def setup(bot: KumaBot) -> None:
    await bot.add_cog(WeeklyUpdateReminder(bot))
