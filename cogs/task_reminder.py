import datetime

import discord
from discord import app_commands
from discord.ext import commands

from config.googlesheet import (
    AGCM,
    GOOGLESHEET_ID,
    ROLEID_MAP,
)
from core.bot_core import KumaBot

MAX_TIME = datetime.datetime.strptime("9999/12/31", "%Y/%m/%d")


class TaskReminder(commands.Cog):
    def __init__(self, bot: KumaBot) -> None:
        self.bot = bot
        self.completed_states = "已完成"

    async def _fetch_data(self) -> bool:
        try:
            # Create a Google Sheets API service
            agc = await AGCM.authorize()
            ss = await agc.open_by_key(GOOGLESHEET_ID)
            worksheet = await ss.get_worksheet(2)
            result = await worksheet.get_all_values()
        except Exception as e:
            print(f"Error accessing Google Sheet: {e}")
            return False

        self.title = result[0]
        self.values = result[1:]
        return True

    # TODO: Add group query function

    @app_commands.command(name="todo", description="查詢成員的未完成任務")
    @app_commands.describe(member="查詢的成員（預設：自己）")
    async def get_user_todo_tasks(
        self, interaction: discord.Interaction, member: discord.Member | None = None
    ) -> None:
        try:
            is_data_fetched = await self._fetch_data()
            assert is_data_fetched is True, "Failed to fetch data from Google Sheet"

            target = member or interaction.user
            target_id = str(target.id)
            assert isinstance(target, discord.Member), "Target must be a Member"
            target_role_ids = [role.id for role in target.roles]

            # Try to get the name used in the sheet for this discord id
            user_mapping = self.bot.user_mapping.get(target_id, None)
            mapped_name = user_mapping.get("name", None) if user_mapping else None
            assert mapped_name is not None, "Mapped name must not be None"

            # header order (0-based):
            # 任務, 優先順序, 負責人, 組別, 狀態, 開始日期, 結束日期, 文件, 附註
            title_idx = 0
            priority_idx = 1  # P0, P1, P2, P3
            assignee_idx = 2  # User name
            group_idx = 3  # Team name
            status_idx = 4  # 尚未開始, 進行中, 已完成
            due_idx = 6  # yyyy/mm/dd

            user_tasks = []
            for row in self.values:
                # be defensive about short rows
                if len(row) <= max(status_idx, assignee_idx):
                    continue
                assignee = row[assignee_idx]
                status = row[status_idx].strip() if row[status_idx] else ""
                role_id = (
                    ROLEID_MAP.get(row[group_idx], None)
                    if len(row) > group_idx
                    else None
                )

                add_task = (
                    # Directly assigned task
                    assignee == mapped_name and status != self.completed_states
                ) or (
                    # Shared task for the role
                    assignee == ""
                    and role_id in target_role_ids
                    and status != self.completed_states
                )
                if add_task:
                    task_title = row[title_idx] if len(row) > title_idx else ""
                    priority = row[priority_idx] if len(row) > priority_idx else ""
                    # Change due to datetime object for sorting
                    if len(row) > due_idx and row[due_idx] != "":
                        due = datetime.datetime.strptime(row[due_idx], "%Y/%m/%d")
                    else:
                        due = MAX_TIME
                    user_tasks.append(
                        (task_title, priority, due, status, row[group_idx])
                    )

            assert len(user_tasks) > 0, f"No tasks found for {target.display_name}"

            # Sort with a more meaningful order by:
            # 1. Priority
            # 2. Due date
            # 3. Status
            def sort_key(
                task: tuple[str, str, datetime.datetime, str, str],
            ) -> tuple[int, datetime.datetime, str]:
                priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
                priority = priority_order.get(
                    task[1], 99
                )  # Default to low priority if unknown
                due_date = task[2] if task[2] is not None else MAX_TIME
                status = task[3]
                return (priority, due_date, status)

            user_tasks.sort(key=sort_key)

            lines = []
            last_priority = "Px"
            emoji_map = {"尚未開始": "⏳", "進行中": "🔨"}
            for i, (t, p, d, s, g) in enumerate(user_tasks, start=1):
                if p != last_priority:
                    last_priority = p
                    lines.append(f"### 優先順序 {p}")
                due_display = "----/--/--" if d == MAX_TIME else d.strftime("%Y/%m/%d")
                lines.append(
                    f"{i}. ({g}) {t}: {emoji_map.get(s, '')}{s}（截止：{due_display}）"
                )

            if target == interaction.user:
                header = "你的未完成任務："
            else:
                header = f"{target.display_name} 的未完成任務："

            message = header + "\n" + "\n".join(lines)
            await interaction.response.send_message(message, ephemeral=True)

        except Exception as e:
            print(f"Error in get_user_todo_tasks command: {e}")
            await interaction.response.send_message(f"發生錯誤：{e}", ephemeral=True)


async def setup(bot: KumaBot) -> None:
    await bot.add_cog(TaskReminder(bot))
