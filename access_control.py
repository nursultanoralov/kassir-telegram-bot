import json
import os

ALLOWED_USERS_FILE = "allowed_users.json"

def load_allowed_users():
    """JSON ішінен рұқсат берілген қолданушылар тізімін жүктейді."""
    if not os.path.exists(ALLOWED_USERS_FILE):
        return []
    with open(ALLOWED_USERS_FILE, "r") as f:
        return json.load(f)

def save_allowed_users(users):
    """Рұқсат етілген қолданушылар тізімін JSON-ға сақтайды."""
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(users, f)

def is_allowed(user_id):
    """Қолданушы ID рұқсат берілгендер тізімінде бар ма?"""
    return user_id in load_allowed_users()

def add_user(user_id):
    """Жаңа қолданушыны рұқсат берілгендер тізіміне қосады (егер жоқ болса)."""
    users = load_allowed_users()
    if user_id not in users:
        users.append(user_id)
        save_allowed_users(users)
