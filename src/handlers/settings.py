from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from src.keyboards.settings_kbs import get_settings_keyboard
from src.settings_store import update_user_setting, get_user_settings

router = Router()

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    user_id = message.from_user.id
    user_settings = get_user_settings(user_id)
    
    # Update defaults if missing
    ar = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "photo")
    magic = user_settings.get("magic_prompt", True)
    res = user_settings.get("resolution", "Standard")

    text = (
        "⚙️ Настройки бота\n\n"
        f"📐 Соотношение сторон: {ar}\n"
        f"🎨 Стиль: {style}\n"
        f"✨ Magic Prompt: {'Вкл' if magic else 'Выкл'}\n"
        f"📺 Разрешение: {res}"
    )
    await message.answer(text, reply_markup=get_settings_keyboard())

@router.callback_query(F.data == "settings_model")
async def settings_model_callback(callback: CallbackQuery):
    await callback.answer("В данной версии доступна только модель Gemini Flash", show_alert=True)

@router.callback_query(F.data.startswith("set_"))
async def setting_callback(callback: CallbackQuery):
    # data format: set_action_value
    # e.g. set_ar_16:9, set_style_photo
    
    parts = callback.data.split("_")
    action = parts[1]
    value = parts[2]
    
    user_id = callback.from_user.id
    
    if action == "ar":
        update_user_setting(user_id, "aspect_ratio", value)
        setting_name = "Соотношение сторон"
    elif action == "style":
        update_user_setting(user_id, "style", value)
        setting_name = "Стиль"
    else:
        await callback.answer("Неизвестная настройка")
        return
    
    # Refresh message text to show new settings
    user_settings = get_user_settings(user_id)
    ar = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "photo")
    magic = user_settings.get("magic_prompt", True)
    res = user_settings.get("resolution", "Standard")

    text = (
        "⚙️ Настройки бота\n\n"
        f"📐 Соотношение сторон: {ar}\n"
        f"🎨 Стиль: {style}\n"
        f"✨ Magic Prompt: {'Вкл' if magic else 'Выкл'}\n"
        f"📺 Разрешение: {res}"
    )
    
    await callback.message.edit_text(text, reply_markup=get_settings_keyboard())
    await callback.answer(f"{setting_name} изменено на {value}")
