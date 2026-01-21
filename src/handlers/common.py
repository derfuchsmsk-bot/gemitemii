from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from src.keyboards.main_menu import get_main_keyboard

router = Router()

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Привет! Я бот с поддержкой Google Gemini.\n"
        "Выбери режим работы ниже:",
        reply_markup=get_main_keyboard()
    )

@router.message(Command("help"))
@router.message(F.text == "❓ Помощь")
async def cmd_help(message: Message):
    text = (
        "🤖 Инструкция:\n\n"
        "1. Чат (Gemini): Обычное общение с ИИ.\n"
        "2. Nano Banana Pro: Генерация и редактирование изображений.\n"
        "3. Настройки: Выбор модели и параметров картинок."
    )
    await message.answer(text)
