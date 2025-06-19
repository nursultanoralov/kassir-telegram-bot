import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import os
import json

# Railway т.б. ортаға GOOGLE_CREDENTIALS деп сақталған JSON құпияны жүктейміз
creds_info = json.loads(os.getenv("GOOGLE_CREDENTIALS"))

# Авторизация
scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
creds = Credentials.from_service_account_info(creds_info, scopes=scope)
client = gspread.authorize(creds)

SPREADSHEET_NAME = "Kassir Reports"

def save_to_sheet(branch, username, user_id, values, total):
    sheet = client.open(SPREADSHEET_NAME)
    try:
        worksheet = sheet.worksheet(branch)
    except gspread.WorksheetNotFound:
        worksheet = sheet.add_worksheet(title=branch, rows=1000, cols=20)

    today = datetime.now().strftime("%d-%m-%Y")  # Күн-ай-жыл

    def fmt(n): return f"{int(n):,}".replace(",", " ") if n else 0

    row = [
        today,
        username,
        str(user_id),
        fmt(values.get("Kaspi Pay1", 0)),
        fmt(values.get("Kaspi Pay2", 0)),
        fmt(values.get("Halyk bank1", 0)),
        fmt(values.get("Halyk bank2", 0)),
        fmt(values.get("Талон", 0)),
        fmt(values.get("Сертификат", 0)),
        fmt(values.get("Наличка", 0)),
        fmt(values.get("Гости", 0)),
        fmt(values.get("Сотрудники", 0)),
        f"*{fmt(total)}*"  # Жирный ету үшін Telegram-да ғана, Sheets-та `*` қалуы мүмкін
    ]

    worksheet.append_row(row)

