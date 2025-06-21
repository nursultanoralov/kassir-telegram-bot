import json
import os

ALLOWED_USERS_FILE = "allowed_users.json"

def load_allowed_users():
    if not os.path.exists(ALLOWED_USERS_FILE):
        return []
    with open(ALLOWED_USERS_FILE, "r") as f:
        return json.load(f)

def save_allowed_users(users):
    with open(ALLOWED_USERS_FILE, "w") as f:
        json.dump(users, f)

def is_allowed(user_id):
    return user_id in load_allowed_users()

def add_user(user_id):
    users = load_allowed_users()
    if user_id not in users:
        users.append(user_id)
        save_allowed_users(users)

# access_control.py

def add_user(user_id):
    users = load_allowed_users()
    if user_id not in users:
        users.append(user_id)
        save_allowed_users(users)
        print(f"[add_user] Қолданушы қосылды: {user_id}")
    else:
        print(f"[add_user] Қолданушы бұрыннан бар: {user_id}")
