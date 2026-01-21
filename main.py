import uvicorn
from fastapi import FastAPI
from aiogram import Bot, Dispatcher, types
from src.config import settings
from src.bot import main as bot_main # You might need to refactor bot.py to export dp creation
from src.handlers import common, chat, image_gen, settings as settings_handler
from aiogram.fsm.storage.memory import MemoryStorage

app = FastAPI()

# Initialize Bot and Dispatcher here for Webhook
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())
dp.include_router(common.router)
dp.include_router(settings_handler.router)
dp.include_router(image_gen.router)
dp.include_router(chat.router)

@app.on_event("startup")
async def on_startup():
    webhook_info = await bot.get_webhook_info()
    if settings.WEBHOOK_URL and webhook_info.url != settings.WEBHOOK_URL:
        await bot.set_webhook(settings.WEBHOOK_URL)

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