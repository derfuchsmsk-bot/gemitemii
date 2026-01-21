import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Telegram
    BOT_TOKEN: str
    WEBHOOK_URL: str = ""
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: str | None = None
    PROJECT_ID: str
    REGION: str = "us-central1"
    
    # App
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
