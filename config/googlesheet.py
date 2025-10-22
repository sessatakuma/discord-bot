import os

from google.oauth2 import service_account
from googleapiclient.discovery import build

from config.settings import RoleId

GOOGLESHEET_ID = os.getenv("GOOGLESHEET_ID")
assert GOOGLESHEET_ID, "GOOGLESHEET_ID is not set"
GOOGLESHEET_PRIVATE_KEY = os.getenv("GOOGLESHEET_PRIVATE_KEY").replace("\\n", "\n")
assert GOOGLESHEET_PRIVATE_KEY, "GOOGLESHEET_PRIVATE_KEY is not set"
GOOGLESHEET_PRIVATE_KEY_ID = os.getenv("GOOGLESHEET_PRIVATE_KEY_ID")
assert GOOGLESHEET_PRIVATE_KEY_ID, "GOOGLESHEET_PRIVATE_KEY_ID is not set"
GOOGLESHEET_CLIENT_ID = os.getenv("GOOGLESHEET_CLIENT_ID")
assert GOOGLESHEET_CLIENT_ID, "GOOGLESHEET_CLIENT_ID is not set"

GOOGLESHEET_CREDENTIALS = {
    "type": "service_account",
    "project_id": "sessatakuma-471415",
    "private_key_id": GOOGLESHEET_PRIVATE_KEY_ID,
    "private_key": GOOGLESHEET_PRIVATE_KEY,
    "client_email": "get-sheet-bot@sessatakuma-471415.iam.gserviceaccount.com",
    "client_id": GOOGLESHEET_CLIENT_ID,
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/get-sheet-bot%40sessatakuma-471415.iam.gserviceaccount.com",
    "universe_domain": "googleapis.com",
}

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]
GOOGLESHEET_CREDS = service_account.Credentials.from_service_account_info(
    GOOGLESHEET_CREDENTIALS, scopes=SCOPES
)

ROLEID_MAP = {
    "テック班": RoleId.tech.value,
    "デザイン班": RoleId.design.value,
    "コンテンツ班": RoleId.content.value,
    "スタッフ": RoleId.staff.value,
}


def get_user_mapping():
    service = build("sheets", "v4", credentials=GOOGLESHEET_CREDS)
    # Get user data from Google Sheets
    worksheet_name = "成員!F:H"
    try:
        result = (
            service.spreadsheets()
            .values()
            .get(spreadsheetId=GOOGLESHEET_ID, range=worksheet_name)
            .execute()
            .get("values", [])[1:]
        )
    except Exception as e:
        print(f"Error accessing Google Sheet for user mapping: {e}")
        result = []
    # Create a mapping for users
    USER_MAPPING = {}
    for row in result:
        name_in_sheet = row[0]
        discord_id = row[1] if len(row) > 1 else None
        github_id = row[2] if len(row) > 2 else None
        if discord_id and name_in_sheet:
            USER_MAPPING[discord_id] = {"name": name_in_sheet, "github": github_id}
    print(f"Loaded USER_MAPPING for {len(USER_MAPPING)} users:")
    service.close()
    return USER_MAPPING
