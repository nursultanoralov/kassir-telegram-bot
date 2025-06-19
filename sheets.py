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

    today = datetime.now().strftime("%d-%m-%Y")

    def clean(val):
        if isinstance(val, str):
            val = val.replace("тг", "").replace(" ", "").strip()
        return int(val) if val else 0

    row = [
        today,
        username,
        str(user_id),
        clean(values.get("Kaspi Pay1")),
        clean(values.get("Kaspi Pay2")),
        clean(values.get("Halyk bank1")),
        clean(values.get("Halyk bank2")),
        clean(values.get("Талон")),
        clean(values.get("Сертификат")),
        clean(values.get("Наличка")),
        clean(values.get("Гости")),
        clean(values.get("Сотрудники")),
        clean(total)
    ]

    worksheet.append_row(row)
