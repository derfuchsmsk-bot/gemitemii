from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from src.services.vertex_ai import vertex_service
from src.keyboards.settings_kbs import get_image_response_keyboard
from src.keyboards.image_gen_kbs import get_generation_settings_keyboard
from src.states import GenStates
from src.settings_store import get_user_settings, update_user_setting
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "🎨 Nano Banana Pro")
async def image_mode_entry(message: Message, state: FSMContext):
    await state.set_state(GenStates.prompt_wait)
    
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    ar = settings.get("aspect_ratio", "1:1")
    style = settings.get("style", "Фотореализм")
    magic = settings.get("magic_prompt", True)
    
    text = (
        "🎨 **Режим Nano Banana Pro**\n\n"
        "Введите описание картинки, которую хотите создать.\n"
        "Вы можете изменить параметры генерации кнопками ниже перед отправкой текста 👇"
    )
    
    await message.answer(text, reply_markup=get_generation_settings_keyboard(ar, style, magic))
    logger.info(f"User {user_id} entered image generation mode")

@router.callback_query(F.data.startswith("gen_set_"))
async def quick_settings_callback(callback: CallbackQuery, state: FSMContext):
    # Format: gen_set_ar_1:1 or gen_set_style_Name or gen_set_magic_on/off
    parts = callback.data.split("_")
    action = parts[2] # ar, style, magic
    value = parts[3]
    
    user_id = callback.from_user.id
    
    if action == "ar":
        update_user_setting(user_id, "aspect_ratio", value)
    elif action == "style":
        update_user_setting(user_id, "style", value)
    elif action == "magic":
        # Value is 'on' or 'off'
        is_on = (value == "on")
        update_user_setting(user_id, "magic_prompt", is_on)
        
    # Refresh keyboard
    settings = get_user_settings(user_id)
    ar = settings.get("aspect_ratio", "1:1")
    style = settings.get("style", "Фотореализм")
    magic = settings.get("magic_prompt", True)
    
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_generation_settings_keyboard(ar, style, magic)
        )
    except Exception:
        pass 
        
    await callback.answer()

@router.message(GenStates.prompt_wait)
async def process_image_prompt(message: Message, state: FSMContext):
    user_prompt = message.text
    user_id = message.from_user.id
    
    # Get user settings
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "Фотореализм")
    magic_prompt = user_settings.get("magic_prompt", True)
    
    msg = await message.answer(f"🎨 Генерирую изображение...\n(AR: {aspect_ratio}, Style: {style}, Magic: {'ON' if magic_prompt else 'OFF'})")
    
    try:
        # Decide prompt logic based on Magic setting
        if magic_prompt:
            full_user_prompt = (
                f"User request: '{user_prompt}'. "
                f"Desired Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: 1. Create a detailed, creative prompt in English for this image. 2. GENERATE the image."
            )
        else:
            # Direct mode: Just execute what user asked, maybe translate if needed but keep it simple
            full_user_prompt = (
                f"User request: '{user_prompt}'. "
                f"Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image exactly as described. Do not embellish or change the subject significantly."
            )
        
        # Single call to Gemini 3 Image
        image_bytes, model_text = await vertex_service.generate_image(full_user_prompt, aspect_ratio=aspect_ratio)
        
        photo_file = BufferedInputFile(image_bytes, filename="image.png")
        
        await msg.delete()
        
        caption_text = f"✨ {model_text[:900]}..." if len(model_text) > 900 else f"✨ {model_text}"
        if not caption_text.strip() or caption_text == "✨ ...":
             caption_text = f"✨ {user_prompt}"

        result_msg = await message.answer_photo(
            photo=photo_file,
            caption=caption_text,
            reply_markup=get_image_response_keyboard()
        )
        
        # Save necessary data
        # IMPORTANT: We need to check if photo exists and get ID properly
        if result_msg.photo:
            file_id = result_msg.photo[-1].file_id
            await state.update_data(
                last_prompt=user_prompt, # Save ORIGINAL prompt so regen respects current settings
                last_image_id=file_id
            )
        else:
            logger.error("No photo found in result message")
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "img_download")
async def download_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("last_image_id")
    
    logger.info(f"Attempting to download file_id: {file_id}")
    
    if not file_id:
        await callback.answer("⚠️ Файл устарел или не найден. Сгенерируйте заново.", show_alert=True)
        return

    try:
        await callback.message.answer_document(document=file_id, caption="📥 Ваш файл")
        await callback.answer()
    except Exception as e:
        logger.error(f"Failed to send document: {e}")
        await callback.answer("❌ Ошибка отправки файла", show_alert=True)

@router.callback_query(F.data == "img_regenerate")
async def regenerate_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    original_prompt = data.get("last_prompt") # This is now original user prompt
    
    if not original_prompt:
        await callback.answer("⚠️ Нет данных для повтора", show_alert=True)
        return
    
    await callback.answer("🔄 Генерирую заново...")
    
    # Create a fake message object with the original text to reuse process_image_prompt logic
    # This ensures it uses CURRENT settings (AR, Magic, etc.) which might have been changed by user
    # Or, if we want to repeat EXACT settings, we should have saved them in state.
    # Usually "Regenerate" means "Try again with same inputs".
    
    # Reuse logic via function call
    # We need to Mock message object
    from aiogram.types import User, Chat
    
    # Better way: Refactor process_image_prompt to separate logic, but for now lets just call it
    # We need to construct a message-like object
    
    # Actually, simpler: just call the logic code directly here
    user_id = callback.from_user.id
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "Фотореализм")
    magic_prompt = user_settings.get("magic_prompt", True)
    
    msg = await callback.message.answer(f"🎨 Вариант 2...\n(AR: {aspect_ratio}, Style: {style}, Magic: {'ON' if magic_prompt else 'OFF'})")
    
    try:
        if magic_prompt:
            full_user_prompt = (
                f"User request: '{original_prompt}'. "
                f"Desired Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: 1. Create a detailed, creative prompt in English for this image. 2. GENERATE the image."
            )
        else:
            full_user_prompt = (
                f"User request: '{original_prompt}'. "
                f"Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image exactly as described."
            )

        image_bytes, model_text = await vertex_service.generate_image(full_user_prompt, aspect_ratio=aspect_ratio)
        photo_file = BufferedInputFile(image_bytes, filename="image.png")
        
        await msg.delete()
        
        caption_text = f"✨ {model_text[:900]}..." if len(model_text) > 900 else f"✨ {model_text}"
        if not caption_text.strip(): caption_text = f"✨ {original_prompt}"

        result_msg = await callback.message.answer_photo(
            photo=photo_file,
            caption=caption_text,
            reply_markup=get_image_response_keyboard()
        )
        
        if result_msg.photo:
            file_id = result_msg.photo[-1].file_id
            await state.update_data(last_image_id=file_id) # Update ID for download button
            
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")
ж