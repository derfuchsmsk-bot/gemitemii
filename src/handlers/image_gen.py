from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, BufferedInputFile
from aiogram.fsm.context import FSMContext
from src.services.vertex_ai import vertex_service
from src.keyboards.settings_kbs import get_image_response_keyboard
from src.states import GenStates

router = Router()

@router.message(F.text == "🎨 Nano Banana Pro")
async def image_mode_entry(message: Message, state: FSMContext):
    await state.set_state(GenStates.prompt_wait)
    await message.answer("🎨 Режим генерации. Введите описание картинки, которую хотите создать.")

@router.message(GenStates.prompt_wait)
async def process_image_prompt(message: Message, state: FSMContext):
    prompt = message.text
    msg = await message.answer("🎨 Генерирую изображение...")
    
    try:
        # Returns bytes now
        image_bytes = await vertex_service.generate_image(prompt)
        
        # Create input file from bytes
        photo_file = BufferedInputFile(image_bytes, filename="image.png")
        
        await msg.delete()
        await message.answer_photo(
            photo=photo_file,
            caption=f"✨ {prompt}",
            reply_markup=get_image_response_keyboard()
        )
        await state.clear()
    except Exception as e:
        await msg.edit_text(f"❌ Ошибка генерации: {str(e)}")
        await state.clear()
