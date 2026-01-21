# Simple in-memory storage for user settings
# In production, use Redis or Database

USER_SETTINGS = {}

DEFAULT_SETTINGS = {
    "aspect_ratio": "1:1",
    "style": "Фотореализм"
}

def get_user_settings(user_id: int) -> dict:
    return USER_SETTINGS.get(user_id, DEFAULT_SETTINGS.copy())

def update_user_setting(user_id: int, key: str, value: str):
    if user_id not in USER_SETTINGS:
        USER_SETTINGS[user_id] = DEFAULT_SETTINGS.copy()
    USER_SETTINGS[user_id][key] = value
