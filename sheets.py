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

    row = [
        today,
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
        total
    ]

    worksheet.append_row(row)
