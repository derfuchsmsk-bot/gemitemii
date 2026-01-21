from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard() -> ReplyKeyboardMarkup:
    kb = [
        [
            KeyboardButton(text="💬 Чат"),
            KeyboardButton(text="🎨 Текст в фото")
        ],
        [
            KeyboardButton(text="🖼 Фото в фото"),
            KeyboardButton(text="⚙️ Настройки")
        ],
        [
            KeyboardButton(text="❓ Помощь")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)
