import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    WEBHOOK_URL: str | None = None
    TELEGRAM_SECRET_TOKEN: str | None = None
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    PROJECT_ID: str
    REGION: str = "us-central1"
    
    # App
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    @property
    def is_production(self) -> bool:
        return os.getenv("K_SERVICE") is not None

    def validate(self):
        if not self.BOT_TOKEN:
            raise ValueError("BOT_TOKEN is required")
        if not self.PROJECT_ID:
            raise ValueError("PROJECT_ID is required")
        if self.is_production and not self.WEBHOOK_URL:
            raise ValueError("WEBHOOK_URL is required in production")

settings = Settings()
settings.validate()
