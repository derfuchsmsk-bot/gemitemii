import logging
import uvicorn
from fastapi import FastAPI, Header, HTTPException
from aiogram import Bot, Dispatcher, types
from src.config import settings
from src.handlers import common, chat, image_gen, settings as settings_handler
from src.middlewares.throttling import RateLimitMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from starlette.status import HTTP_403_FORBIDDEN
import asyncio
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Initialize Bot and Dispatcher here for Webhook
bot = Bot(token=settings.BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Setup middlewares
dp.message.middleware(RateLimitMiddleware(limit=1.0))

# Include routers
dp.include_router(common.router)
dp.include_router(settings_handler.router)
dp.include_router(image_gen.router)
dp.include_router(chat.router)

@app.on_event("startup")
async def on_startup():
    try:
        webhook_url = settings.WEBHOOK_URL
        if not webhook_url:
            logger.warning("WEBHOOK_URL is not set.")
            return

        # Ensure /webhook suffix
        if not webhook_url.endswith("/webhook"):
            webhook_url = f"{webhook_url.rstrip('/')}/webhook"
            settings.WEBHOOK_URL = webhook_url

        logger.info(f"Setting webhook to {webhook_url}")
        # Always set webhook on startup to be sure, and clear any old secret tokens
        await bot.set_webhook(
            url=webhook_url,
            drop_pending_updates=True
        )
    except Exception as e:
        logger.error(f"Startup error: {e}")

@app.post("/webhook")
async def webhook(update: dict):
    telegram_update = types.Update(**update)
    await dp.feed_update(bot, telegram_update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    # Basic check to see if bot is responsive
    try:
        await bot.get_me()
        return {"status": "healthy", "bot": "ok"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)