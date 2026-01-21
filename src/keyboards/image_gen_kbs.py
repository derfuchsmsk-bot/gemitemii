from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

def get_generation_settings_keyboard(current_ar: str, current_style: str, magic_prompt: bool) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    
    # Row 1: Magic Prompt Toggle
    magic_text = "✨ Magic: ON" if magic_prompt else "⚪ Magic: OFF"
    builder.row(InlineKeyboardButton(text=magic_text, callback_data=f"gen_set_magic_{'off' if magic_prompt else 'on'}"))

    # Row 2: Aspect Ratio toggles (Popular)
    builder.row(
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '1:1' else ''}1:1", callback_data="gen_set_ar_1:1"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '16:9' else ''}16:9", callback_data="gen_set_ar_16:9"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '9:16' else ''}9:16", callback_data="gen_set_ar_9:16")
    )
    # Row 3: More Aspect Ratios
    builder.row(
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '4:3' else ''}4:3", callback_data="gen_set_ar_4:3"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '3:4' else ''}3:4", callback_data="gen_set_ar_3:4"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '3:2' else ''}3:2", callback_data="gen_set_ar_3:2"),
        InlineKeyboardButton(text=f"{'✅ ' if current_ar == '2:3' else ''}2:3", callback_data="gen_set_ar_2:3")
    )

    # Row 4: Styles
    builder.row(
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Фотореализм' else ''}Фото", callback_data="gen_set_style_Фотореализм"),
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Аниме/Арт' else ''}Арт", callback_data="gen_set_style_Аниме/Арт"),
        InlineKeyboardButton(text=f"{'✅ ' if current_style == 'Без стиля' else ''}Нет", callback_data="gen_set_style_Без стиля")
    )
    
    return builder.as_markup()
