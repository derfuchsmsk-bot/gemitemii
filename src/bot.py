import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from src.config import settings
from src.handlers import common, chat, image_gen, settings as settings_handler

# Logging setup
logging.basicConfig(level=logging.INFO)

async def main():
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register routers
    dp.include_router(common.router)
    dp.include_router(settings_handler.router)
    dp.include_router(image_gen.router)
    dp.include_router(chat.router) # Chat router last to catch text messages

    # Start polling (for local dev) or webhook (for cloud run)
    # For MVP local dev:
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
