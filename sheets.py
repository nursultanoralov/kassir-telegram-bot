import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

# Railway немесе локалды ортада GOOGLE_CREDENTIALS қоршаған айнымалынан жүктеу
creds_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "Kassir Reports"

def save_to_sheet(branch, username, user_id, values):
    sheet = client.open(SPREADSHEET_NAME)
    try:
        worksheet = sheet.worksheet(branch)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=branch, rows=1000, cols=20)

    now = datetime.now()
    date_value = now.date()                      # күн (формат: YYYY-MM-DD)
    time_value = now.strftime("%H:%M")           # уақыт (формат: 14:35)

    row = [
    str(date_value),
    time_value,
    username,
    str(user_id),
    values.get("Kaspi Pay-1", 0),
    values.get("Kaspi Pay-2", 0),
    values.get("Halyk-1", 0),
    values.get("Halyk-2", 0),
    values.get("Баллом", 0),
    values.get("Сертификат", 0),
    values.get("Наличка", 0),
    values.get("Талон", 0),
    values.get("Сотрудники", 0),  # 🔹 Жаңа қосылған баған
    # Жалпы сумма автоматты түрде формуламен есептеледі
]


    worksheet.append_row(row, value_input_option="USER_ENTERED")
