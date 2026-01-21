from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_settings_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Model selection
    builder.row(InlineKeyboardButton(text="🧠 Модель: Gemini Flash (Быстро)", callback_data="settings_model"))
    
    # Aspect Ratio settings header
    builder.row(InlineKeyboardButton(text="📐 Соотношение сторон:", callback_data="ignore"))
    
    # Aspect Ratios
    builder.row(
        InlineKeyboardButton(text="1:1", callback_data="set_ar_1:1"),
        InlineKeyboardButton(text="16:9", callback_data="set_ar_16:9"),
        InlineKeyboardButton(text="9:16", callback_data="set_ar_9:16")
    )
    
    # Style settings header
    builder.row(InlineKeyboardButton(text="🎨 Стиль:", callback_data="ignore"))
    
    # Styles
    builder.row(
        InlineKeyboardButton(text="Фото", callback_data="set_style_photo"),
        InlineKeyboardButton(text="Арт", callback_data="set_style_art"),
        InlineKeyboardButton(text="Нет", callback_data="set_style_none")
    )
    
    return builder.as_markup()

def get_chat_response_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Сгенерировать заново", callback_data="chat_regenerate"),
        InlineKeyboardButton(text="🗑 Очистить контекст", callback_data="chat_clear")
    )
    return builder.as_markup()

def get_image_response_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="🔄 Еще вариант", callback_data="img_regenerate"),
        InlineKeyboardButton(text="📥 Скачать файл", callback_data="img_download")
    )
    builder.row(
        InlineKeyboardButton(text="✏️ Редактировать", callback_data="img_edit")
    )
    return builder.as_markup()
