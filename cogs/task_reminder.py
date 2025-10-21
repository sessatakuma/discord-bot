import discord
import datetime
from discord import app_commands
from discord.ext import commands
from googleapiclient.discovery import build
from config.googlesheet import (
    ROLEID_MAP,
    GOOGLESHEET_ID,
    GOOGLESHEET_CREDS,
    get_user_mapping,
)

MAX_TIME = datetime.datetime.strptime("9999/12/31", "%Y/%m/%d")


class TaskReminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.user_mapping = get_user_mapping()
        self.bot = bot
        self.completed_states = "已完成"

    def _access_data(self):
        WORKSHEET_NAME = "工作表"
        try:
            # Create a Google Sheets API service
            service = build("sheets", "v4", credentials=GOOGLESHEET_CREDS)
            result = (
                service.spreadsheets()
                .values()
                .get(spreadsheetId=GOOGLESHEET_ID, range=WORKSHEET_NAME)
                .execute()
            )
            service.close()
        except Exception as e:
            print(f"Error accessing Google Sheet: {e}")
            return False

        self.title = result.get("values", [])[0]
        self.values = result.get("values", [])[1:]
        return True

    # TODO: Add group query function

    @app_commands.command(name="todo", description="查詢成員的未完成任務")
    @app_commands.describe(member="查詢的成員（預設：自己）")
    async def get_user_todo_tasks(
        self, interaction: discord.Interaction, member: discord.Member = None
    ):
        # Ensure latest data
        if not self._access_data():
            await interaction.response.send_message(
                "無法連線至 Google Sheet，請稍後再試。", ephemeral=True
            )
            return

        target = member or interaction.user
        target_id = str(target.id)
        target_role_ids = [role.id for role in target.roles]

        # Try to get the name used in the sheet for this discord id
        user_mapping = self.user_mapping.get(target_id, None)
        mapped_name = user_mapping.get("name", None) if user_mapping else None
        if mapped_name is None:
            await interaction.response.send_message(
                "找不到此成員在名單中的對應名稱，請聯絡管理員。", ephemeral=True
            )
            return

        # header order (0-based): 任務, 優先順序, 負責人, 組別, 狀態, 開始日期, 結束日期, 文件, 附註
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
                ROLEID_MAP.get(row[group_idx], None) if len(row) > group_idx else None
            )

            add_task = (
                # Directly assigned task
                assignee == mapped_name and status != self.completed_states
            ) or (
                # Shared task for the role
                assignee == "" and role_id in target_role_ids
            )
            if add_task:
                task_title = row[title_idx] if len(row) > title_idx else ""
                priority = row[priority_idx] if len(row) > priority_idx else ""
                # Change due to datetime object for sorting
                if len(row) > due_idx and row[due_idx] != "":
                    due = datetime.datetime.strptime(row[due_idx], "%Y/%m/%d")
                else:
                    due = MAX_TIME
                user_tasks.append((task_title, priority, due, status, row[group_idx]))

        if not user_tasks:
            if target == interaction.user:
                await interaction.response.send_message(
                    "你目前沒有未完成的任務。", ephemeral=True
                )
            else:
                await interaction.response.send_message(
                    f"{target.display_name} 目前沒有未完成的任務。", ephemeral=True
                )
            return

        # Sort with a more meaningful order by:
        # 1. Priority
        # 2. Due date
        # 3. Status
        def sort_key(task):
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


async def setup(bot: commands.Bot):
    await bot.add_cog(TaskReminder(bot))
