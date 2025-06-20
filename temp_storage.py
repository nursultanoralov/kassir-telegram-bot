# temp_storage.py
import json
import os  # ← МІНДЕТТІ түрде осы жол болу керек

TEMP_FILE = "temp_storage.json"


def load_temp_storage():
    if not os.path.exists(TEMP_FILE):
        return {}
    with open(TEMP_FILE, "r") as f:
        return json.load(f)


def save_temp_storage(data):
    with open(TEMP_FILE, "w") as f:
        json.dump(data, f)


def add_temp_entry(user_id, entry):
    data = load_temp_storage()
    data[str(user_id)] = entry
    save_temp_storage(data)


def get_temp_entry(user_id):
    return load_temp_storage().get(str(user_id))


def remove_temp_entry(user_id):
    data = load_temp_storage()
    if str(user_id) in data:
        del data[str(user_id)]
        save_temp_storage(data)


def all_temp_entries():
    return load_temp_storage()
