import logging
import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from src.config import settings
from src.handlers import common, chat, image_gen, settings as settings_handler
from aiogram.fsm.storage.memory import MemoryStorage

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Bot and Dispatcher here for Webhook
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Include routers
dp.include_router(common.router)
dp.include_router(settings_handler.router)
dp.include_router(image_gen.router)
dp.include_router(chat.router)

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    webhook_url = settings.WEBHOOK_URL
    
    if webhook_url:
        if webhook_info.url != webhook_url:
            logger.info(f"Setting webhook to {webhook_url}")
            await bot.set_webhook(webhook_url)
        else:
            logger.info("Webhook already set correctly.")
    else:
        logger.warning("WEBHOOK_URL is not set. Bot will not receive updates unless polling is used or webhook was set previously.")

@app.post("/webhook")
async def webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8080)