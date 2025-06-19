import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# Авторизация
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
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
