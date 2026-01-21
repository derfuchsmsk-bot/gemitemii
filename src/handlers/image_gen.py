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
    
    text = (
        "🎨 **Режим Nano Banana Pro**\n\n"
        "Введите описание картинки, которую хотите создать.\n"
        "Вы можете изменить параметры генерации кнопками ниже перед отправкой текста 👇"
    )
    
    await message.answer(text, reply_markup=get_generation_settings_keyboard(ar, style))
    logger.info(f"User {user_id} entered image generation mode")

@router.callback_query(F.data.startswith("gen_set_"))
async def quick_settings_callback(callback: CallbackQuery, state: FSMContext):
    # Format: gen_set_ar_1:1 or gen_set_style_Name
    parts = callback.data.split("_")
    action = parts[2] # ar or style
    value = parts[3]
    
    user_id = callback.from_user.id
    
    if action == "ar":
        update_user_setting(user_id, "aspect_ratio", value)
    elif action == "style":
        update_user_setting(user_id, "style", value)
        
    # Refresh keyboard to show checkmarks
    settings = get_user_settings(user_id)
    ar = settings.get("aspect_ratio", "1:1")
    style = settings.get("style", "Фотореализм")
    
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_generation_settings_keyboard(ar, style)
        )
    except Exception:
        pass # Ignore if content didn't change
        
    await callback.answer()

@router.message(GenStates.prompt_wait)
async def process_image_prompt(message: Message, state: FSMContext):
    user_prompt = message.text
    user_id = message.from_user.id
    
    # Get user settings
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "Фотореализм")
    
    msg = await message.answer(f"🎨 Придумываю детали и генерирую...\n(AR: {aspect_ratio}, Style: {style})")
    
    try:
        # Step 1: Enhance prompt using Gemini Text model
        # This makes short prompts like "beautiful photo" into detailed descriptions
        enhancement_instruction = (
            f"You are an expert prompt engineer for AI image generation. "
            f"The user wants an image described as: '{user_prompt}'. "
            f"The desired style is '{style}'. "
            f"Create a detailed, creative, and high-quality prompt in English for this image. "
            f"Describe lighting, composition, textures, and mood. "
            f"Output ONLY the prompt text, nothing else."
        )
        
        # Use existing text generation service (Gemini 1.5/3 Pro)
        enhanced_prompt = await vertex_service.generate_text(enhancement_instruction, model_type="pro")
        
        # Log for debugging quality
        logger.info(f"Original prompt: {user_prompt} -> Enhanced: {enhanced_prompt}")
        
        # Step 2: Generate Image with the enhanced prompt
        # We append Aspect Ratio info for the model
        full_prompt = f"{enhanced_prompt}. Aspect Ratio: {aspect_ratio}"
        
        image_bytes = await vertex_service.generate_image(full_prompt, aspect_ratio=aspect_ratio)
        photo_file = BufferedInputFile(image_bytes, filename="image.png")
        
        await msg.delete()
        
        # Send photo
        # Show the enhanced prompt in caption so user knows what was generated
        # Truncate caption if too long (Telegram limit is 1024 chars)
        caption_text = f"✨ {enhanced_prompt[:900]}..." if len(enhanced_prompt) > 900 else f"✨ {enhanced_prompt}"
        
        result_msg = await message.answer_photo(
            photo=photo_file,
            caption=caption_text,
            reply_markup=get_image_response_keyboard()
        )
        
        # Save necessary data
        file_id = result_msg.photo[-1].file_id
        
        await state.update_data(
            last_prompt=enhanced_prompt, # Save the ENHANCED prompt for regeneration
            last_image_id=file_id
        )
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}")
        await msg.edit_text(f"❌ Ошибка: {str(e)}")

@router.callback_query(F.data == "img_download")
async def download_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("last_image_id")
    
    if not file_id:
        await callback.answer("⚠️ Файл не найден (возможно, бот был перезагружен)", show_alert=True)
        return

    await callback.message.answer_document(document=file_id, caption="📥 Ваш файл")
    await callback.answer()

@router.callback_query(F.data == "img_regenerate")
async def regenerate_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    prompt = data.get("last_prompt")
    
    if not prompt:
        await callback.answer("⚠️ Нет данных для повтора", show_alert=True)
        return
    
    await callback.answer("🔄 Генерирую заново...")
    
    # Simulate message sending to reuse logic
    # We create a dummy message object to call process_image_prompt
    # This is a bit hacky but avoids code duplication. 
    # Better way: refactor generation logic into standalone function.
    
    # Let's just refactor slightly or call logic directly.
    # Calling logic directly is safer.
    
    user_id = callback.from_user.id
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "Фотореализм")
    full_prompt = f"{prompt}. Style: {style}"
    
    msg = await callback.message.answer(f"🎨 Генерирую вариант 2...\n(AR: {aspect_ratio}, Style: {style})")
    
    try:
        image_bytes = await vertex_service.generate_image(full_prompt, aspect_ratio=aspect_ratio)
        photo_file = BufferedInputFile(image_bytes, filename="image.png")
        
        await msg.delete()
        result_msg = await callback.message.answer_photo(
            photo=photo_file,
            caption=f"✨ {prompt} (Вариант 2)",
            reply_markup=get_image_response_keyboard()
        )
        
        # Update state with NEW file_id
        file_id = result_msg.photo[-1].file_id
        await state.update_data(last_image_id=file_id)
        
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка: {str(e)}")
