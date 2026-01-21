import os
import logging
from pydantic_settings import BaseSettings

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    WEBHOOK_URL: str | None = None
    TELEGRAM_SECRET: str | None = os.getenv("TELEGRAM_SECRET")
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    PROJECT_ID: str = os.getenv("PROJECT_ID", "")
    GCS_BUCKET_NAME: str | None = os.getenv("GCS_BUCKET_NAME")
    REGION: str = os.getenv("REGION", "global")
    
    # App
    PORT: int = int(os.getenv("PORT", "8080"))
    HOST: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

    @property
    def is_production(self) -> bool:
        return os.getenv("K_SERVICE") is not None

    def validate(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        
        if not self.PROJECT_ID:
            # Don't fail during build/local if PROJECT_ID is missing but not needed immediately
            logger.warning("PROJECT_ID is not set. Firestore and Vertex AI may fail.")
        if self.is_production and not self.WEBHOOK_URL:
            logger.warning("WEBHOOK_URL is not set in production. Bot will not receive updates.")

settings = Settings()
settings.validate()
