from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_generation_settings_keyboard(current_ar: str, current_style: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Row 1: Aspect Ratio toggles
    # We can show a few popular ones
    builder.row(
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '1:1' else ''}1:1", callback_data="gen_set_ar_1:1"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '16:9' else ''}16:9", callback_data="gen_set_ar_16:9"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '9:16' else ''}9:16", callback_data="gen_set_ar_9:16")
    )
    
    # Row 2: Styles
    builder.row(
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Фотореализм' else ''}Фото", callback_data="gen_set_style_Фотореализм"),
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Аниме/Арт' else ''}Арт", callback_data="gen_set_style_Аниме/Арт"),
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Без стиля' else ''}Нет", callback_data="gen_set_style_Без стиля")
    )
    
    return builder.as_markup()
