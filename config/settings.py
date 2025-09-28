import os
from enum import Enum

from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
API_URL = os.getenv("API_URL")

GUILD_ID = 1265707637836615730


class RoleId(Enum):
    staff = 1366967981862551593
    design = 1377276884177518702
    tech = 1377276760466391112
    content = 1377276456953974896


class GeneralChannelId(Enum):
    staff = 1366969424892006541
    design = 1372167584249679933
    tech = 1377276305413898312
    content = 1377275852311494776


class MeetingChannelId(Enum):
    staff = 1366969280553554020
    design = 1377278148617699368
    tech = 1377277888931303434
    content = 1377278272676692111


# Cogs to load
COGS = [
    "cogs.dict_query",
    "cogs.usage_query",
    "cogs.control",
    "cogs.mark_text",
    "cogs.event_reminder",
    "cogs.meeting_reminder",
]
