import logging
import uvicorn
from fastapi import FastAPI, Header, HTTPException, BackgroundTasks
from aiogram import Bot, Dispatcher, types
from src.config import settings
from src.handlers import common, chat, image_gen, settings as settings_handler
from src.middlewares.throttling import RateLimitMiddleware
from aiogram.fsm.storage.memory import MemoryStorage
from starlette.status import HTTP_403_FORBIDDEN
from contextlib import asynccontextmanager
import asyncio
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting up application...")
        # Check if project_id is available
        if not settings.PROJECT_ID:
            logger.error("PROJECT_ID environment variable is missing!")
            
        webhook_url = settings.WEBHOOK_URL
        if webhook_url and bot:
            if not webhook_url.endswith("/webhook"):
                webhook_url = f"{webhook_url.rstrip('/')}/webhook"
                settings.WEBHOOK_URL = webhook_url

            logger.info(f"Setting webhook to {webhook_url}")
            # Ensure bot and dp are ready
            await bot.set_webhook(
                url=webhook_url,
                drop_pending_updates=True,
                secret_token=settings.TELEGRAM_SECRET
            )
            logger.info("Webhook set successfully")
        elif not bot:
            logger.error("Bot not initialized, cannot set webhook")
        else:
            logger.warning("WEBHOOK_URL is not set. Bot will not receive updates.")
    except Exception as e:
        logger.error(f"Critical startup error: {e}", exc_info=True)
    
    yield
    
    try:
        logger.info("Shutting down application...")
        # Optional: await bot.delete_webhook()
    except Exception as e:
        logger.error(f"Shutdown error: {e}")

app = FastAPI(lifespan=lifespan)

# Initialize Bot and Dispatcher here for Webhook
try:
    bot = Bot(token=settings.BOT_TOKEN or "dummy_token")
    dp = Dispatcher(storage=MemoryStorage())
except Exception as e:
    logger.error(f"Error initializing Bot/Dispatcher: {e}")
    # We still need these defined for the webhook handler
    bot = None
    dp = None

# Setup middlewares
if dp:
    dp.message.middleware(RateLimitMiddleware(limit=1.0))

    # Include routers
    dp.include_router(common.router)
    dp.include_router(image_gen.router) # Moved UP
    dp.include_router(settings_handler.router)
    dp.include_router(chat.router) # Moved DOWN

@app.post("/webhook")
async def webhook(
    update: dict, 
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str = Header(None)
):
    if not bot or not dp:
        logger.error("Webhook received but bot/dp not initialized")
        raise HTTPException(status_code=500, detail="Bot not initialized")

    if settings.TELEGRAM_SECRET and x_telegram_bot_api_secret_token != settings.TELEGRAM_SECRET:
        logger.warning("Unauthorized webhook request")
        raise HTTPException(status_code=HTTP_403_FORBIDDEN, detail="Forbidden")

    telegram_update = types.Update(**update)
    background_tasks.add_task(dp.feed_update, bot, telegram_update)
    return {"ok": True}

@app.get("/")
async def health():
    return {"status": "ok"}

@app.get("/health")
async def health_check():
    # Basic check to see if bot is responsive
    try:
        if bot:
            await bot.get_me()
            return {"status": "healthy", "bot": "ok"}
        return {"status": "degraded", "bot": "not_initialized"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}") # Added print for direct feedback
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)