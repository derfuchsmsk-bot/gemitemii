from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from src.services.vertex_ai import vertex_service
from src.keyboards.settings_kbs import get_image_response_keyboard
from src.keyboards.image_gen_kbs import get_generation_settings_keyboard
from src.states import GenStates
from src.settings_store import get_user_settings, update_user_setting
from aiogram.exceptions import TelegramBadRequest
import logging

logger = logging.getLogger(__name__)

router = Router()

@router.message(F.text == "🎨 Nano Banana Pro")
async def image_mode_entry(message: Message, state: FSMContext):
    await state.set_state(GenStates.prompt_wait)
    
    user_id = message.from_user.id
    settings = get_user_settings(user_id)
    ar = settings.get("aspect_ratio", "1:1")
    style = settings.get("style", "photo")
    magic = settings.get("magic_prompt", True)
    res = settings.get("resolution", "Standard")
    
    text = (
        "🎨 **Режим Nano Banana Pro**\n\n"
        "Введите описание картинки, которую хотите создать.\n"
        "Вы можете изменить параметры генерации кнопками ниже перед отправкой текста 👇"
    )
    
    await message.answer(text, reply_markup=get_generation_settings_keyboard(ar, style, magic, res))
    logger.info(f"User {user_id} entered image generation mode")

@router.callback_query(F.data.startswith("gen_set_"))
async def quick_settings_callback(callback: CallbackQuery, state: FSMContext):
    # Format: gen_set_ar_1:1 or gen_set_style_photo or gen_set_magic_on/off or gen_set_res_4K
    try:
        parts = callback.data.split("_")
            
        action = parts[2] # ar, style, magic, res
        value = parts[3]
        
        user_id = callback.from_user.id
        
        if action == "ar":
            update_user_setting(user_id, "aspect_ratio", value)
        elif action == "style":
            update_user_setting(user_id, "style", value)
        elif action == "magic":
            is_on = (value == "on")
            update_user_setting(user_id, "magic_prompt", is_on)
        elif action == "res":
            update_user_setting(user_id, "resolution", value)
            
        # Refresh keyboard
        user_settings = get_user_settings(user_id)
        ar = user_settings.get("aspect_ratio", "1:1")
        style = user_settings.get("style", "photo")
        magic = user_settings.get("magic_prompt", True)
        res = user_settings.get("resolution", "Standard")
        
        await callback.message.edit_reply_markup(
            reply_markup=get_generation_settings_keyboard(ar, style, magic, res)
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e).lower():
            pass
        else:
            logger.error(f"Telegram error: {e}")
    except Exception as e:
        logger.error(f"Settings callback error: {e}", exc_info=True)
        
    await callback.answer()

@router.message(GenStates.prompt_wait)
async def process_image_prompt(message: Message, state: FSMContext):
    user_prompt = message.text
    user_id = message.from_user.id
    
    # Get user settings
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "photo")
    magic_prompt = user_settings.get("magic_prompt", True)
    resolution = user_settings.get("resolution", "Standard")
    
    magic_status = "ON" if magic_prompt else "OFF"
    msg = await message.answer(f"🎨 Генерирую... (AR: {aspect_ratio}, Style: {style}, Magic: {magic_status}, Res: {resolution})")
    
    try:
        # Construct prompt suffix based on resolution
        res_prompt = ""
        if resolution == "HD":
            res_prompt = "High definition, sharp details."
        elif resolution == "4K":
            res_prompt = "4k resolution, 8k textures, highly detailed, ultra-sharp focus."

        if magic_prompt:
            full_user_prompt = (
                f"User request: '{user_prompt}'. "
                f"Desired Style: {style}. {res_prompt} "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image. "
                f"In your text response, provide ONLY a very brief, one-sentence description of the image in Russian. "
                f"DO NOT include your reasoning, thoughts, or internal monologue."
            )
        else:
            full_user_prompt = (
                f"User request: '{user_prompt}'. "
                f"Style: {style}. {res_prompt} "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image exactly as described. Do not embellish. "
                f"In your text response, provide ONLY a very brief, one-sentence description of the image in Russian."
            )
        
        # Single call to Gemini 3 Image
        image_bytes, model_text = await vertex_service.generate_image(full_user_prompt, aspect_ratio=aspect_ratio)
        
        # Save to GCS for later download
        gcs_file_name = await vertex_service.upload_to_gcs(image_bytes)
        
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
        
        if result_msg.photo:
            file_id = result_msg.photo[-1].file_id
            await state.update_data(
                last_prompt=user_prompt,
                last_image_id=file_id,
                gcs_file_name=gcs_file_name # Save reference to GCS
            )
        else:
            logger.error("No photo found in result message")
        
    except Exception as e:
        logger.error(f"Image generation failed: {e}", exc_info=True)
        try:
            await msg.edit_text("❌ Извините, произошла ошибка при генерации изображения. Попробуйте другой запрос.")
        except Exception:
            # If we can't edit the message (e.g. it was deleted), just log it
            # and DO NOT raise exception, otherwise Telegram will retry endlessly
            logger.error("Could not send error message to user.")

@router.callback_query(F.data == "img_download")
async def download_image(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    gcs_file_name = data.get("gcs_file_name")
    
    await callback.answer("⏳ Скачиваю оригинал из Google Cloud...")

    try:
        if gcs_file_name:
            # Method 1: Get original from GCS (Best Quality)
            image_bytes = await vertex_service.download_from_gcs(gcs_file_name)
            if image_bytes:
                document_file = BufferedInputFile(image_bytes, filename="original_image.png")
                await callback.message.answer_document(
                    document=document_file, 
                    caption="📥 Оригинал из Google Cloud Storage (100% качество)"
                )
                return

        # Method 2: Fallback to Telegram servers if GCS fails or file not in GCS
        file_id = None
        if callback.message.photo:
            file_id = callback.message.photo[-1].file_id
        
        if not file_id:
            file_id = data.get("last_image_id")

        if file_id:
            bot = callback.bot
            file = await bot.get_file(file_id)
            image_io = await bot.download_file(file.file_path)
            document_file = BufferedInputFile(image_io.read(), filename="image.png")
            await callback.message.answer_document(document=document_file, caption="📥 Файл (через Telegram)")
        else:
            await callback.answer("❌ Файл не найден", show_alert=True)
            
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await callback.answer("❌ Ошибка при скачивании", show_alert=True)

@router.callback_query(F.data == "img_edit")
async def start_image_edit(callback: CallbackQuery, state: FSMContext):
    # Store the file_id in state when user clicks 'Edit' 
    # so we know WHICH image to edit even if state was lost
    if callback.message.photo:
        file_id = callback.message.photo[-1].file_id
        await state.update_data(last_image_id=file_id)
        
        # Also try to extract original prompt from caption if possible
        caption = callback.message.caption or ""
        if caption.startswith("✨ "):
            await state.update_data(last_prompt=caption[2:].split("...")[0])

    await state.set_state(GenStates.edit_wait)
    await callback.message.answer(
        "✏️ **Режим редактирования**\n\n"
        "Опишите, что вы хотите изменить в этом изображении.\n"
        "Например: 'Сделай небо красным' или 'Добавь кота на стул'."
    )
    await callback.answer()

@router.message(GenStates.edit_wait)
async def process_image_edit(message: Message, state: FSMContext):
    data = await state.get_data()
    file_id = data.get("last_image_id")
    
    # If file_id still missing, try to look at the previous message in chat history 
    # (though AIogram doesn't make this easy, the state update in 'img_edit' should fix it)
    
    edit_prompt = message.text

    if not file_id:
        await message.answer("⚠️ Исходное изображение не найдено. Нажмите кнопку 'Редактировать' под нужным изображением еще раз.")
        await state.set_state(GenStates.prompt_wait)
        return

    msg = await message.answer("🎨 Редактирую изображение...")

    try:
        # Download file from Telegram
        bot = message.bot
        file = await bot.get_file(file_id)
        image_io = await bot.download_file(file.file_path)
        image_bytes = image_io.read()

        # Call Vertex AI
        edited_image_bytes = await vertex_service.edit_image(image_bytes, edit_prompt)
        
        # Save edited version to GCS
        new_gcs_file = await vertex_service.upload_to_gcs(edited_image_bytes)
        
        photo_file = BufferedInputFile(edited_image_bytes, filename="edited_image.png")
        
        await msg.delete()
        result_msg = await message.answer_photo(
            photo=photo_file,
            caption=f"✨ Отредактировано: {edit_prompt}",
            reply_markup=get_image_response_keyboard()
        )
        
        if result_msg.photo:
            await state.update_data(
                last_image_id=result_msg.photo[-1].file_id,
                gcs_file_name=new_gcs_file
            )
            
    except Exception as e:
        logger.error(f"Image edit failed: {e}", exc_info=True)
        await msg.edit_text("❌ Извините, произошла ошибка при редактировании изображения.")
    
    await state.set_state(GenStates.prompt_wait)

@router.callback_query(F.data == "img_regenerate")
async def regenerate_image(callback: CallbackQuery, state: FSMContext):
    # Try to recover prompt from state or caption
    data = await state.get_data()
    original_prompt = data.get("last_prompt")
    
    if not original_prompt and callback.message.caption:
        caption = callback.message.caption
        if caption.startswith("✨ "):
            original_prompt = caption[2:].split("...")[0]

    if not original_prompt:
        await callback.answer("⚠️ Нет данных для повтора. Напишите новый запрос.", show_alert=True)
        return
    
    await callback.answer("🔄 Генерирую заново...")
    
    user_id = callback.from_user.id
    user_settings = get_user_settings(user_id)
    aspect_ratio = user_settings.get("aspect_ratio", "1:1")
    style = user_settings.get("style", "photo")
    magic_prompt = user_settings.get("magic_prompt", True)
    
    magic_status = "ON" if magic_prompt else "OFF"
    msg = await callback.message.answer(f"🎨 Вариант 2...\n(AR: {aspect_ratio}, Style: {style}, Magic: {magic_status})")
    
    try:
        if magic_prompt:
            full_user_prompt = (
                f"User request: '{original_prompt}'. "
                f"Desired Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image. "
                f"In your text response, provide ONLY a very brief, one-sentence description of the image in Russian. "
                f"DO NOT include your reasoning, thoughts, or internal monologue."
            )
        else:
            full_user_prompt = (
                f"User request: '{original_prompt}'. "
                f"Style: {style}. "
                f"Aspect Ratio: {aspect_ratio}. "
                f"Action: GENERATE the image exactly as described. "
                f"In your text response, provide ONLY a very brief, one-sentence description of the image in Russian."
            )

        image_bytes, model_text = await vertex_service.generate_image(full_user_prompt, aspect_ratio=aspect_ratio)
        
        # Save to GCS
        new_gcs_file = await vertex_service.upload_to_gcs(image_bytes)
        
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
            await state.update_data(
                last_image_id=file_id,
                gcs_file_name=new_gcs_file
            )
            
    except Exception as e:
        logger.error(f"Regeneration failed: {e}", exc_info=True)
        try:
            await msg.edit_text("❌ Извините, произошла ошибка при повторной генерации.")
        except:
            pass
