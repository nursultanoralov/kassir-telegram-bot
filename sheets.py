import gspread
import json
import os
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

credentials_dict = json.loads(os.getenv("GOOGLE_CREDENTIALS"))  # Railway-де сақталған JSON
creds = ServiceAccountCredentials.from_json_keyfile_dict(credentials_dict, scope)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "Kassir Reports"

def save_to_sheet(branch, username, user_id, values, total):
    sheet = client.open(SPREADSHEET_NAME)
    try:
        worksheet = sheet.worksheet(branch)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=branch, rows=1000, cols=20)

    today = datetime.now().strftime("%d-%m-%Y")

    row = [
        today,
        username,
        str(user_id),
        values.get("Kaspi Pay1", 0),
        values.get("Kaspi Pay2", 0),
        values.get("Halyk bank1", 0),
        values.get("Halyk bank2", 0),
        values.get("Талон", 0),
        values.get("Сертификат", 0),
        values.get("Наличка", 0),
        values.get("Гости", 0),
        values.get("Сотрудники", 0),
        total
    ]

    worksheet.append_row(row)
