from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from src.keyboards.settings_kbs import get_settings_keyboard

router = Router()

@router.message(F.text == "⚙️ Настройки")
async def settings_menu(message: Message):
    await message.answer("⚙️ Настройки бота:", reply_markup=get_settings_keyboard())

@router.callback_query(F.data.startswith("set_"))
async def setting_callback(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    value = callback.data.split("_")[2]
    
    await callback.answer(f"Настройка {action} изменена на {value}")
