import discord
from discord import app_commands
from discord.ext import commands
from googleapiclient.discovery import build
from google.oauth2 import service_account
from config.settings import GOOGLE_SHEET_ID

SERVICE_ACCOUNT_FILE = 'googlesheet_access_key.json'
SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES
)
service = build('sheets', 'v4', credentials=creds)

class TaskReminder(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.completed_states = "已完成"
        
    def _access_data(self):
        WORKSHEET_NAME = '工作表'
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=WORKSHEET_NAME
        ).execute()
        self.title = result.get('values', [])[0]
        self.values = result.get('values', [])[1:]
        
    def _access_user_mapping(self):
        WORKSHEET_NAME = '成員!F:G'
        result = service.spreadsheets().values().get(
            spreadsheetId=GOOGLE_SHEET_ID,
            range=WORKSHEET_NAME
        ).execute()
        # Create a mapping from Discord ID to name in sheet
        self.user_mapping = {row[1]: row[0] for row in result.get('values', [])[1:]}
        
    # TODO: Add group query function
    
    @app_commands.command(name="todo", description="查詢成員的未完成任務")
    @app_commands.describe(member="查詢的成員（預設：自己）")
    async def get_user_todo_tasks(self, interaction: discord.Interaction, member: discord.Member = None):
        # Ensure latest data
        self._access_data()
        self._access_user_mapping()

        target = member or interaction.user
        target_id = str(target.id)

        # Try to get the name used in the sheet for this discord id
        mapped_name = self.user_mapping.get(target_id)
        if mapped_name is None:
            await interaction.response.send_message("找不到此成員在名單中的對應名稱，請聯絡管理員。", ephemeral=True)
            return

        # header order (0-based): 任務, 優先順序, 負責人, 組別, 狀態, 開始日期, 結束日期, 文件, 附註
        title_idx = 0
        priority_idx = 1
        assignee_idx = 2
        status_idx = 4
        due_idx = 6


        user_tasks = []
        for row in self.values:
            # be defensive about short rows
            if len(row) <= max(status_idx, assignee_idx):
                continue
            assignee = row[assignee_idx]
            status = row[status_idx].strip() if row[status_idx] else ""
            if assignee == mapped_name and status != self.completed_states:
                # build a compact representation
                task_title = row[title_idx] if len(row) > title_idx else ""
                priority = row[priority_idx] if len(row) > priority_idx else ""
                due = row[due_idx] if len(row) > due_idx else ""
                user_tasks.append((task_title, priority, due, status))

        if not user_tasks:
            if target == interaction.user:
                await interaction.response.send_message("你目前沒有未完成的任務。", ephemeral=True)
            else:
                await interaction.response.send_message(f"{target.display_name} 目前沒有未完成的任務。", ephemeral=True)
            return

        # format message (limit to 20 tasks to avoid huge messages)
        lines = []
        for i, (t, p, d, s) in enumerate(user_tasks[:20], start=1):
            lines.append(f"{i}. {t}（優先：{p}，截止：{d}，狀態：{s}）")

        footer = ""
        if len(user_tasks) > 20:
            footer = f"\n還有 {len(user_tasks) - 20} 項未列出。"

        if target == interaction.user:
            header = "你的未完成任務："
        else:
            header = f"{target.display_name} 的未完成任務："

        await interaction.response.send_message(header + "\n" + "\n".join(lines) + footer, ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(TaskReminder(bot))
