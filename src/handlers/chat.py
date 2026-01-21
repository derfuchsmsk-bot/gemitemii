from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from src.services.vertex_ai import vertex_service
from src.keyboards.settings_kbs import get_chat_response_keyboard
from src.settings_store import db
import logging

logger = logging.getLogger(__name__)

router = Router()

def get_context_ref(user_id: int):
    if db:
        return db.collection("chat_contexts").document(str(user_id))
    return None

@router.message(F.text == "🔘 Чат (Gemini)")
async def chat_mode_entry(message: Message):
    await message.answer("💬 Режим чата активирован. Пиши любой вопрос!")

@router.message(F.text & ~F.text.startswith("/"))
async def chat_handler(message: Message):
    user_id = message.from_user.id
    history = []
    
    ref = get_context_ref(user_id)
    if ref:
        doc = ref.get()
        if doc.exists:
            history = doc.to_dict().get("history", [])
    
    msg = await message.answer("⏳ Думаю...")
    
    try:
        response = await vertex_service.generate_text(message.text, history=history)
        
        if ref:
            history.append({"role": "user", "parts": [message.text]})
            history.append({"role": "model", "parts": [response]})
            # Keep last 10 messages (5 turns)
            ref.set({"history": history[-10:]})
        
        await msg.edit_text(response, reply_markup=get_chat_response_keyboard())
    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        await msg.edit_text("❌ Произошла ошибка при обращении к AI. Попробуйте позже.")

@router.callback_query(F.data == "chat_clear")
async def clear_context(callback: CallbackQuery):
    user_id = callback.from_user.id
    ref = get_context_ref(user_id)
    if ref:
        ref.delete()
    await callback.message.edit_text("🗑 Контекст очищен!")
    await callback.answer()
