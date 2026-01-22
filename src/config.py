import os
import logging
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict

# Настройка логирования
logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    Настройки приложения. 
    Pydantic автоматически ищет переменные окружения с именами, совпадающими с полями класса.
    """
    
    # Telegram
    BOT_TOKEN: str = ""
    WEBHOOK_URL: Optional[str] = None
    TELEGRAM_SECRET: Optional[str] = None
    
    # Google Cloud
    GOOGLE_APPLICATION_CREDENTIALS: Optional[str] = None
    PROJECT_ID: str = ""
    GCS_BUCKET_NAME: Optional[str] = None
    REGION: str = "global"
    
    # App / Server
    # Cloud Run автоматически передает PORT. Pydantic подхватит его из переменных окружения.
    PORT: int = 8080
    HOST: str = "0.0.0.0"

    # Конфигурация Pydantic
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def is_production(self) -> bool:
        """Определяет, запущено ли приложение в облаке (Google Cloud Run)."""
        return os.getenv("K_SERVICE") is not None

    def validate(self):
        """
        Проверка обязательных параметров. 
        Выводит предупреждения вместо исключений, чтобы избежать падения при запуске.
        """
        if not self.BOT_TOKEN:
            logger.warning("⚠️  BOT_TOKEN не установлен. Бот не сможет подключиться к Telegram.")
        
        if not self.PROJECT_ID:
            logger.warning("⚠️  PROJECT_ID не установлен. Firestore и Vertex AI могут не работать.")
        
        if self.is_production and not self.WEBHOOK_URL:
            logger.warning("⚠️  WEBHOOK_URL не задан в режиме production. Бот не сможет получать обновления.")

# Инициализация настроек
settings = Settings()
settings.validate()